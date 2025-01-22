"""
Api routes
"""

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .utils import create_new_job, get_jobs_data

async def get_jobs(request: Request):
    """
    Get list of jobs
    """
    try:
        data = await get_jobs_data(arq_conn=request.state.arq_conn)
        response = JSONResponse(
            content={"status": "success", **data},
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

api_routes = [
    Route(path='/jobs', endpoint=get_jobs, methods=["GET", ], name="get_jobs"),
    Route(path='/jobs', endpoint=create_job, methods=["POST", ], name="create_job"),
]
