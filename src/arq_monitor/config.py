"""
Config
"""

from arq.connections import RedisSettings
from jinja2 import Environment, FileSystemLoader
import os
from starlette.config import Config
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

config = Config(".env")
REDIS_ADDRESS = config("REDIS_ADDRESS", default="redis://localhost:6379")
ARQ_CONN_CONFIG = RedisSettings.from_dsn(REDIS_ADDRESS)

app_dir = os.path.abspath(os.path.dirname(__file__))
assets_dir = os.path.join(app_dir, "frontend/assets")
template_dir = os.path.join(app_dir, "frontend/templates")

def app_context(request: Request) -> dict:
    return {"request": request, }

jinja_env = Environment(
    autoescape=True,
    loader=FileSystemLoader(searchpath=template_dir)
)
TEMPLATES = Jinja2Templates(env=jinja_env, context_processors=[app_context, ],)

STATIC = StaticFiles(directory=assets_dir)
