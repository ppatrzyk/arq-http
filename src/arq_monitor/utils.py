import asyncio
from arq.connections import ArqRedis
from arq.jobs import JobDef, JobResult

import itertools

def _value_repr(val):
    """
    Data respresentation for json responses
    """
    if isinstance(val, (tuple, list, set, )):
        return tuple(_value_repr(entry) for entry in val)
    elif isinstance(val, dict):
        return {k: _value_repr(v) for k, v in val.items()}
    elif isinstance(val, (bool, int, float, )):
        return val
    else:
        return str(val)

def _job_def_reformat(job: JobDef):
    """
    Job definition reformat
    """
    data = {
        "enqueue_time": job.enqueue_time.isoformat(),
        "job_try": job.job_try,
        "job_id": job.job_id,
        "function": job.function,
        "args": _value_repr(job.args),
        "kwargs": _value_repr(job.kwargs),
    }
    return data

def _job_result_reformat(job: JobResult):
    """
    Get job result representation + compute stats
    """
    time_inqueue = job.start_time - job.enqueue_time
    time_exec = job.finish_time - job.start_time
    data = {
        "time_inqueue": time_inqueue.total_seconds(),
        "time_exec": time_exec.total_seconds(),
        "start_time": job.start_time.isoformat(),
        "finish_time": job.finish_time.isoformat(),
        "success": job.success,
        "result": job.result,
        "queue_name": job.queue_name,
        **_job_def_reformat(job),
    }
    return data

async def get_job_results(arq_conn: ArqRedis):
    """
    Lit job results
    """
    all_job_results = await arq_conn.all_job_results()
    by_queue = dict()
    for queue, jobs in itertools.groupby(all_job_results, lambda job: job.queue_name):
        by_queue[queue] = {"results": tuple(_job_result_reformat(job) for job in jobs)}
    return by_queue

async def get_queue(arq_conn: ArqRedis, queue_name: str):
    """
    List items in a queue
    """
    queued_jobs_raw = await arq_conn.queued_jobs(queue_name=queue_name)
    queued_jobs = tuple(_job_def_reformat(job) for job in queued_jobs_raw)
    return queued_jobs


async def create_new_job(arq_conn: ArqRedis, kwargs: dict):
    """
    Create new job
    """
    job = await arq_conn.enqueue_job(**kwargs)
    return job
