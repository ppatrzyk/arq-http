# arq-monitor

Dashboard and HTTP api for [arq job queue](https://github.com/python-arq/arq).

## Installation

### Run with docker

```
docker run -e REDIS_ADDRESS="redis://localhost:6379" -p 8000:8000 pieca/arq-monitor:0.1
```

### Install Python package

```
# install
TODO

# start rerver
arq-monitor
```

### Configuration

Configuration is made via environment variables.

| variable | description |
| --- | --- |
| REDIS_ADDRESS | redis address, default: redis://localhost:6379 |
| DEFAULT_REFRESH | default refresh frequency of dashboards (in seconds), default: 5.0 |

Refresh frequency can also be controlled by query parameter when opening dashboards:

http://localhost:8000/dashboard/arq:myqueue?refresh=2

## Usage

### Links

- dashboards per queue: http://localhost:8000/dashboard/
- api docs: http://localhost:8000/api/docs

### Api

- list jobs

```
curl -X GET http://localhost:8000/api/jobs
```

- schedule job

Keyword arguments to [enqueue_job](https://arq-docs.helpmanual.io/#arq.connections.ArqRedis.enqueue_job) need to be _posted_ as _json_ data.

Assuming you have a function [`get_random_numbers`](src/arq_monitor/worker.py#L15):

```
curl -X POST \
    -d '{"_queue_name": "arq:myqueue", "function": "get_random_numbers", "n": 10}' \
    http://localhost:8000/api/jobs
```

## Screenshots

### Dashboard
![dashboard](screenshots/dashboard.png)

### Job listing
![job_list](screenshots/job_list.png)

### Job details
![job_details](screenshots/job_details.png)

## local dev

```
# run valkey
docker run -p 6380:6379 valkey/valkey:8.0.2

# run dashboard
REDIS_ADDRESS="redis://localhost:6380" arq-monitor

# run example worker
REDIS_ADDRESS="redis://localhost:6380" arq arq_monitor.worker.WorkerSettings

# create jobs
parallel -I ,, curl -X POST -d \'{\"_queue_name\": \"arq:myqueue\", \"function\": \"get_random_numbers\", \"n\": ,,}\' http://localhost:8000/api/jobs ::: {100000..100100}
parallel -N0 curl -X POST -d \'{\"_queue_name\": \"arq:myqueue\", \"function\": \"random_sleep\"}\' http://localhost:8000/api/jobs ::: {1..10}

# docker build
docker build -t pieca/arq-monitor:0.2 .
```

## Known limitations

- to be triggered via http api, jobs cannot take custom classes as arguments
- dashboard needs to be manually refreshed after running unknown function

TODO:
- optional disable table generation if too many items
- push only if new data available
- better filters based on job status
- abort endpoint
