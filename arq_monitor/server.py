from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import contextlib
from datetime import datetime, timedelta, UTC
import logging

from arq import create_pool

from .config import ARQ_CONN_CONFIG
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
        # TODO asyncio gather
        for queue_name in data.keys():
            data[queue_name]["queue"] = await get_queue(arq_conn=request.state.arq_conn, queue_name=queue_name)
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

exception_handlers = {
    HTTPException: http_exception
}

@contextlib.asynccontextmanager
async def lifespan(_app):
    arq_conn = await create_pool(ARQ_CONN_CONFIG)
    yield {"arq_conn": arq_conn}

routes=[
    Route(path='/jobs', endpoint=get_jobs, methods=["GET", ]),
    Route(path='/jobs', endpoint=create_job, methods=["POST", ]),
]

app = Starlette(
    exception_handlers=exception_handlers,
    lifespan=lifespan,
    routes=routes
)
