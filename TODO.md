> Can we use a database? What for? SQL or NoSQL?

Like I said in the README we have to store the result if using asynchronous tasks - Celery - and it can be done in a database or in a cache - Redis -
but I think the best solution for such case would be using files and that would result in the need of creating crons for removing old files. Other than
that, we can store some data for making the calls "easier" for the API's consumer like what I have done storing the *username* and the *pattern* on Redis
so only the request id has to be sent for checking and fetching calls.

> How can we protect the api from abusing it?

The implementation of rate limits would avoid such abuse as the API's consumer would have a limited budget for using it.

> How can we deploy the application in a cloud environment?

Dockerizing and using Kubernetes are good steps for duing that as it is very easy to replicate pods and to create new instances

> How can we be sure the application is alive and works as expected when deployed into a cloud environment?

Kubernetes would help here as well as it already has "health checks" and docker-compose has rules for restarting the containers as well.
