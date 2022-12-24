from asyncio import current_task
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from url_shortener.conf import config

engine = create_async_engine(f"{config.database_uri}?charset=utf8mb4")


@lru_cache
def create_session() -> async_scoped_session:
    Session = async_scoped_session(
        sessionmaker(
            autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
        ),
        current_task,
    )
    return Session


async def get_session() -> AsyncGenerator[async_scoped_session, None]:
    Session = create_session()
    try:
        yield Session
    finally:
        await Session.remove()
