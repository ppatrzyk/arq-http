from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Mount, Route

import contextlib
from arq import create_pool

from .api import api_routes
from .config import ARQ_CONN_CONFIG, logger, STATIC
from .dashboard import dashboard_routes

async def dashboard_redirect(request: Request):
    """
    Redirect to dashboard
    """
    url = request.url_for("dashboard:list_dashboards")
    response = RedirectResponse(url=url)
    return response

async def http_exception(request: Request, exc: HTTPException):
    content = {
        "status": "error",
        "detail": exc.detail
    }
    return JSONResponse(content=content, status_code=exc.status_code)

exception_handlers = {
    HTTPException: http_exception
}

@contextlib.asynccontextmanager
async def lifespan(_app):
    arq_conn = await create_pool(ARQ_CONN_CONFIG)
    yield {"arq_conn": arq_conn}

routes=[
    Route(path='/', endpoint=dashboard_redirect, methods=["GET", ], name="dashboard_redirect"),
    Mount(path="/api", routes=api_routes, name="api"),
    Mount(path="/dashboard", routes=dashboard_routes, name="dashboard"),
    Mount(path="/static", app=STATIC, name="static"),
]

app = Starlette(
    exception_handlers=exception_handlers,
    lifespan=lifespan,
    routes=routes
)
