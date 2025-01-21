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
from arq.connections import ArqRedis

from .config import ARQ_CONN_CONFIG, logger, STATIC, TEMPLATES
from .utils import compute_stats, create_new_job, get_jobs_data

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
        data = await get_jobs_data(arq_conn=request.state.arq_conn)
        response = JSONResponse(
            content={"updated_at": updated_at, "status": "success", **data},
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
    Get dashboard page
    """
    data = {}
    response = TEMPLATES.TemplateResponse(
        request=request,
        name="dashboard.html.jinja",
        context=data
    )
    return response

async def dashboard_data_gen(inner_send_chan: MemoryObjectSendStream, arq_conn: ArqRedis):
    """
    adapted from https://github.com/sysid/sse-starlette/blob/main/examples/no_async_generators.py#L22
    """
    async with inner_send_chan:
        try: 
            while True:
                # TODO push only if data has changed?
                await anyio.sleep(1.0)
                jobs_data = await get_jobs_data(arq_conn)
                jobs_data = await compute_stats(jobs_data)
                # TODO put data and return template
                # "queue-items"
                # "queue-stats"
                # "jobs-data"
                # "jobs-stats"
                data = {
                    "event": "dashboard-data",
                    "data": jobs_data,
                }
                await inner_send_chan.send(data)
        except anyio.get_cancelled_exc_class() as e:
            with anyio.move_on_after(1, shield=True):
                close_msg = {"closing": True, }
                await inner_send_chan.send(close_msg)
                raise e

async def get_dashboard_data(request: Request):
    """
    Get dashboard data
    """
    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=10)
    arq_conn = request.state.arq_conn
    response = EventSourceResponse(
        data_sender_callable=partial(dashboard_data_gen, send_chan, arq_conn),
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
    Route(path='/dashboard-data', endpoint=get_dashboard_data, methods=["GET", ], name="get_dashboard_data"),
    Route(path='/jobs', endpoint=get_jobs, methods=["GET", ], name="get_jobs"),
    Route(path='/jobs', endpoint=create_job, methods=["POST", ], name="create_job"),
    Mount("/static", app=STATIC, name="static"),
]

app = Starlette(
    exception_handlers=exception_handlers,
    lifespan=lifespan,
    routes=routes
)
