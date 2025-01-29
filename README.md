# arq-monitor

_in progress_

Dashboard and HTTP api for [arq task queue](https://github.com/python-arq/arq).

## Installation

### Run with docker

```
docker run -e REDIS_ADDRESS="redis://localhost:6379" -p 8000:8000 pieca/arq-monitor:0.1
```

### Install from PyPi

```
todo
```

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

```
curl -X POST \
    -d '{"_queue_name": "arq:myqueue", "function": "get_random_numbers", "n": 10}' \
    http://localhost:8000/api/jobs
```

TODO:
    config how often data is pushed to frontend
    fix api spec, no args, kwargs on the same level additionalproperties
    reorder sections?
    datatables-bottom standard margins

```
docker build -t pieca/arq-monitor:0.2 .
```

## local run

```
# run valkey
docker run -p 6380:6379 valkey/valkey:8.0.2

# run dashboard
REDIS_ADDRESS="redis://localhost:6380" arq-monitor

# run example worker
REDIS_ADDRESS="redis://localhost:6380" arq arq_monitor.worker.WorkerSettings

# create tasks
parallel -I ,, curl -X POST -d \'{\"_queue_name\": \"arq:myqueue\", \"function\": \"get_random_numbers\", \"n\": ,,}\' http://localhost:8000/api/jobs ::: {100000..100100}
parallel -N0 curl -X POST -d \'{\"_queue_name\": \"arq:myqueue\", \"function\": \"random_sleep\"}\' http://localhost:8000/api/jobs ::: {1..10}
```

## Known limitations

- to be triggered via http api, tasks cannot take custom classes as arguments
- dashboard needs to be manually refreshed after running unknown function
