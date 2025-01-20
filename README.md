# arq-monitor

```
arq arq_monitor.worker.WorkerSettings

uvicorn arq_monitor.server:app
arq-monitor
```

```
curl -X POST -d '{"_queue_name": "arq:myqueue", "function": "get_random_numbers", "n": 5}' http://localhost:8000/jobs
```

TODO:
    separate /api prefix + generate schema
    verify if data included in pip package
    https://setuptools.pypa.io/en/latest/userguide/datafiles.html
