from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = create_async_engine(settings.database.url, echo=False, pool_pre_ping=True)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session_context():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()