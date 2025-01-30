"""
Config
"""

from arq.connections import RedisSettings
from jinja2 import Environment, FileSystemLoader
import logging
import os
from starlette.config import Config
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

logger = logging.getLogger('uvicorn.error')

config = Config(".env")
DEFAULT_REFRESH = float(config("DEFAULT_REFRESH", default=5.0))
REDIS_ADDRESS = config("REDIS_ADDRESS", default="redis://localhost:6379")
ARQ_CONN_CONFIG = RedisSettings.from_dsn(REDIS_ADDRESS)

app_dir = os.path.abspath(os.path.dirname(__file__))
assets_dir = os.path.join(app_dir, "frontend/assets")
template_dir = os.path.join(app_dir, "frontend/templates")

def app_context(request: Request) -> dict:
    return {"request": request, }

JINJA_ENV = Environment(
    autoescape=True,
    loader=FileSystemLoader(searchpath=template_dir)
)
TEMPLATES = Jinja2Templates(env=JINJA_ENV, context_processors=[app_context, ],)

STATIC = StaticFiles(directory=assets_dir)
