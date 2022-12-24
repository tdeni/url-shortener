import logging

from redis import Redis

from url_shortener.conf import config

logger = logging.getLogger("apscheduler")
redis_connection = Redis(config.redis_host, config.redis_port)
