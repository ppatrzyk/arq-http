"""
Config
"""

from arq.connections import RedisSettings
from starlette.config import Config

config = Config(".env")
REDIS_ADDRESS = config("REDIS_ADDRESS", default="redis://localhost:6379")
ARQ_CONN_CONFIG = RedisSettings.from_dsn(REDIS_ADDRESS)
