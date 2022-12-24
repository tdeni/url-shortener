import logging
from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Integer, String, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from url_shortener.conf import config
from url_shortener.database.connection import create_session

logger = logging.getLogger("apscheduler")


Base = declarative_base()


class LinkModel(Base):
    __tablename__ = "link"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    user = Column(String(36))
    subpart = Column(String(1024))
    url = Column(String(2048))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def create(
        cls, session: AsyncSession, user: str, subpart: str, url: str
    ) -> "LinkModel":
        obj = cls(user=user, subpart=subpart, url=url)
        session.add(obj)
        return obj

    @classmethod
    async def list_paginated(
        cls, session: AsyncSession, user: str, page: int, limit: int
    ) -> tuple[list["LinkModel"], int, int]:
        skip = (page - 1) * limit
        count = await session.execute(
            select(func.count(cls.id)).filter(cls.user == user)
        )
        max_page = round(count.scalar_one() / limit) or 1
        next_page = None if page >= max_page else page + 1
        result = await session.execute(
            select(cls)
            .filter(cls.user == user)
            .limit(limit)
            .offset(skip)
            .order_by(desc(cls.created_at))
        )
        return result.scalars().all(), next_page, max_page

    @classmethod
    async def get_url(cls, session: AsyncSession, subpart: str) -> "LinkModel":
        result = await session.execute(select(cls).filter(cls.subpart == subpart))
        return result.scalar()

    @classmethod
    async def subpart_exists(cls, session: AsyncSession, subpart: str) -> bool:
        result = await session.execute(
            select(func.count(cls.id)).filter(LinkModel.subpart == subpart)
        )
        return result.scalar_one() != 0

    @classmethod
    async def remove_old_urls(cls):
        session = create_session()
        time = datetime.utcnow() - timedelta(minutes=config.mysql_max_age)
        count = await session.execute(
            select(func.count(cls.id)).filter(cls.created_at <= time)
        )
        await session.execute(delete(cls).where(cls.created_at <= time))
        await session.commit()
        logger.info(f"Scheduler: {count.scalar_one()} url deleted from database")
