"""
Config
"""

from arq.connections import RedisSettings

# TODO take from env var / option, 6379 default
REDIS_ADDRESS = "redis://localhost:6380"
ARQ_CONN_CONFIG = RedisSettings.from_dsn(REDIS_ADDRESS)
