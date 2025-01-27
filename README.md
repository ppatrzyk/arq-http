# arq-monitor

_in progress_

Dashboard and HTTP api for [arq task queue](https://github.com/python-arq/arq).

tl;dr

```
docker run -e REDIS_ADDRESS="redis://localhost:6379" -p 8000:8000 pieca/arq-monitor:0.1
```

TODO:
    show items in queue 0
    show job status in table
    config how often data is pushed to frontend

```
docker build -t pieca/arq-monitor:0.1 .
```

## local run

```
# run valkey
docker run -p 6380:6379 --network arq valkey/valkey:8.0.2

# run dashboard
REDIS_ADDRESS="redis://localhost:6380" arq-monitor

# run example worker
REDIS_ADDRESS="redis://localhost:6380" arq arq_monitor.worker.WorkerSettings

# create tasks
parallel -I ,, curl -X POST -d \'{\"_queue_name\": \"arq:myqueue\", \"function\": \"get_random_numbers\", \"n\": ,,}\' http://localhost:8000/api/jobs ::: {100..200}
```
