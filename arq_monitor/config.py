"""
Config
"""

from arq.connections import RedisSettings

# TODO take from env var / option
REDIS_ADDRESS = "redis://localhost:6379"
ARQ_CONN_CONFIG = RedisSettings.from_dsn(REDIS_ADDRESS)
