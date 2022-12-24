import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from url_shortener.conf import config

logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.DEBUG)

scheduler = AsyncIOScheduler(
    {
        "apscheduler.jobstores.default": {
            "type": "sqlalchemy",
            "url": config.database_uri_sync,
        }
    }
)
