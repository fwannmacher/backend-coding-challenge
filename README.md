In the given 1.5 hours for implementing the solution I didn't have time for implementing error handling nor test unfortunatelly. I really wanted
to do that but it ended taking way more time to setup Docker with Celery than I expected.

### Why Celery? 
> Implement handling of huge gists
As huge gists may take a long time for fetching I thought that using asynchronous task and giving the possibility for checking its status
would be a good way for handling it.

### Why Redis?
redis is really simple to integrate and setup using Docker and it can be used as backend for Celery. Other than that we needed a way for
storing the result for searchs. Probably the best solution would be writing the result to files but given the time constraints and the
fact that I already had Redis up and running I ended using it.


## How to run
After having *Docker* and *docker-compose* installed run the following command in the project's root directory

```bash
$ docker-compose build
$ docker-compose up
```

These will create the containers and start the application server witch will be available on [http://localhost:8000](http://localhost:8000)

Follwoing and example call using *curl*

```bash
$ curl -X POST localhost:8000/api/v1/search \
    -d '{"username":"justdionysus","pattern":"import requests"}' \
    -H "Content-Type: application/json"
```

Such call will return a request id wich will be used for check the task status and for fetching the result. The response will look like the following

```bash
{
  "request_id": "4a6867b3-0686-4f95-a080-d93fc2537b30"
}
```

For checking the task status the request id is used in the URL as the follwoing

```bash
$ curl -X GET localhost:8000/api/v1/search/4a6867b3-0686-4f95-a080-d93fc2537b30
```

And it results in something like
```bash
{
  "status": "SUCCESS"
}
```

When the status returned is **SUCCESS** then the result can be fetched as the follwoing
```bash
$ curl -X GET localhost:8000/api/v1/search_result/4a6867b3-0686-4f95-a080-d93fc2537b30
```

And the result will look like
```bash
{
  "matches": [
    {
      "comments": 0,
      ...
      "user": null
    }
  ],
  "pattern": "import requests",
  "status": "success",
  "username": "justdionysus"
}
```
