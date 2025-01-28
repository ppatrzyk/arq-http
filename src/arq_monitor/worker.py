"""
Sample worker config

Run with:
arq worker.WorkerSettings
"""

from asyncio import sleep
from datetime import datetime, timedelta, UTC
from random import random
from statistics import mean

from .config import ARQ_CONN_CONFIG

async def get_random_numbers(ctx: dict, n: int):
    assert n >= 0, "n must be positive"
    numbers = tuple(random() for _ in range(n))
    return mean(numbers)

async def random_sleep(ctx: dict):
    t = 1 + random()
    await sleep(t)
    return t

class WorkerSettings:
    timezone = UTC
    redis_settings = ARQ_CONN_CONFIG
    queue_name="arq:myqueue"
    max_jobs = 5
    allow_abort_jobs = True
    functions = [get_random_numbers, random_sleep]
    job_timeout = timedelta(seconds=60)
    keep_result = timedelta(seconds=3600)
