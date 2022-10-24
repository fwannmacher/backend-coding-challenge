"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import json
import os
import re

import requests

from celery import Celery
from celery.result import AsyncResult

from flask import Flask, jsonify, request

from redis import from_url as redis_from_url


app = Flask(__name__)

redis = redis_from_url(os.environ.get("REDIS_URL"), decode_responses=True)

celery = Celery(
    __name__,
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND"),
)


@celery.task(name="search_task", bind=True)
def search_task(self, username, pattern):
    """Task that provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.
    Adds the result to redis to be fetched later.
    """
    redis_key = f"search_result|{self.request.id}"
    gists = gists_for_user(username)

    for gist in gists:
        for file, data in gist.get("files", {}).items():
            response = requests.get(data["raw_url"], stream=True)
            response.raise_for_status()

            if re.search(pattern, response.text):
                redis.rpush(redis_key, json.dumps(gist))

                break


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username: str):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    response = requests.get(f"https://api.github.com/users/{username}/gists")
    response.raise_for_status()

    return response.json()


@app.route("/api/v1/search", methods=['POST'])
def post_search():
    """Calls a task wich provides matches for a single pattern across a single users gists.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the request id to be used for checking the task status and fetching
        the result afterwards.
    """
    post_data = request.get_json()

    username = post_data['username']
    pattern = post_data['pattern']

    task = search_task.delay(username, pattern)
    redis.hset(
        f"search_task|{task.id}",
        mapping={"username": username, "pattern": pattern}
    )

    return jsonify(
        {"request_id": task.id}
    )


@app.route("/api/v1/search/<request_id>", methods=['GET'])
def get_search_status(request_id):
    """Gets the current status for the task linked to the given request id.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the 'status' key indicating the current task status.
    """
    return jsonify(
        {"status": AsyncResult(request_id).status}
    )


@app.route("/api/v1/search_result/<request_id>", methods=['GET'])
def search_result(request_id):
    """Gets the results found for the given request id.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    search_data = redis.hgetall(f"search_task|{request_id}")
    username = search_data["username"]
    pattern = search_data["pattern"]

    return jsonify(
        {
            "status": "success",
            "username": username,
            "pattern": pattern,
            "matches": [
                json.loads(x) for x in redis.lrange(f"search_result|{request_id}", 0, -1)
            ],
        }
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
