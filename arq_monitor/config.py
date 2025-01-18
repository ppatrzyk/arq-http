"""
Config
"""

from arq.connections import RedisSettings
from jinja2 import Environment, FileSystemLoader
import os
from starlette.config import Config
from starlette.templating import Jinja2Templates

config = Config(".env")
REDIS_ADDRESS = config("REDIS_ADDRESS", default="redis://localhost:6379")
ARQ_CONN_CONFIG = RedisSettings.from_dsn(REDIS_ADDRESS)

app_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(app_dir, "templates")
jinja_env = Environment(
    autoescape=True,
    loader=FileSystemLoader(searchpath=template_dir)
)
TEMPLATES = Jinja2Templates(env=jinja_env)
