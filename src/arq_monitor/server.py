from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from sse_starlette.sse import EventSourceResponse

import anyio
from anyio.streams.memory import MemoryObjectSendStream
import asyncio
import contextlib
from datetime import datetime, timedelta, UTC
from functools import partial

from arq import create_pool

from .config import ARQ_CONN_CONFIG, logger, STATIC, TEMPLATES
from .utils import get_job_results, create_new_job, get_queue

async def http_exception(request: Request, exc: HTTPException):
    content = {
        "status": "error",
        "detail": exc.detail
    }
    return JSONResponse(content=content, status_code=exc.status_code)

async def get_jobs(request: Request):
    """
    Get list of jobs
    """
    try:
        updated_at = datetime.now(tz=UTC).isoformat()
        data = await get_job_results(arq_conn=request.state.arq_conn)
        get_queue_tasks = tuple(get_queue(arq_conn=request.state.arq_conn, queue_name=queue_name) for queue_name in data.keys())
        get_queue_results = await asyncio.gather(*get_queue_tasks)
        for i, queue_name in enumerate(data.keys(), start=0):
            data[queue_name]["queue"] = get_queue_results[i]
        response = JSONResponse(
            content={"jobs": data, "updated_at": updated_at, "status": "success"},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response

async def create_job(request: Request):
    """
    Get status of existing job
    """
    try:
        data = await request.json()
        job = await create_new_job(arq_conn=request.state.arq_conn, kwargs=data)
        if job is None:
            response = JSONResponse(
                content={"status": "error", "detail": "job not created"},
                status_code=400
            )
        else:
            response = JSONResponse(
                content={"status": "success", "job_id": job.job_id},
                status_code=201
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response

async def get_dashboard(request: Request):
    """
    Get status of existing job
    """
    data = {}
    response = TEMPLATES.TemplateResponse(
        request=request,
        name="dashboard.html.jinja",
        context=data
    )
    return response

async def sse_gen_test(inner_send_chan: MemoryObjectSendStream):
    """
    adapted from https://github.com/sysid/sse-starlette/blob/main/examples/no_async_generators.py#L22
    """
    async with inner_send_chan:
        try: 
            i = 0
            while True:
                await anyio.sleep(1.0)
                data = dict(event="dashboard-data", data=i)
                await inner_send_chan.send(data)
                i += 1
        except anyio.get_cancelled_exc_class() as e:
            with anyio.move_on_after(1, shield=True):
                close_msg = dict(closing=True)
                await inner_send_chan.send(close_msg)
                raise e

async def get_dashboard_data(request: Request):
    """
    Get dashboard data
    """
    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=10)
    response = EventSourceResponse(
        data_sender_callable=partial(sse_gen_test, send_chan),
        content=recv_chan,
        send_timeout=5
    )
    return response

exception_handlers = {
    HTTPException: http_exception
}

@contextlib.asynccontextmanager
async def lifespan(_app):
    arq_conn = await create_pool(ARQ_CONN_CONFIG)
    yield {"arq_conn": arq_conn}

routes=[
    Route(path='/', endpoint=get_dashboard, methods=["GET", ], name="get_dashboard"),
    Route(path='/get-dashboard-data', endpoint=get_dashboard_data, methods=["GET", ], name="get_dashboard_data"),
    Route(path='/jobs', endpoint=get_jobs, methods=["GET", ], name="get_jobs"),
    Route(path='/jobs', endpoint=create_job, methods=["POST", ], name="create_job"),
    Mount("/static", app=STATIC, name="static"),
]

app = Starlette(
    exception_handlers=exception_handlers,
    lifespan=lifespan,
    routes=routes
)
