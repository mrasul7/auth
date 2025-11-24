from collections.abc import AsyncGenerator
from config import settings
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, 
    create_async_engine
)

engine = create_async_engine(url=settings.DB_URL, echo=False)

async_session_maker = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

async def get_session() -> AsyncGenerator:
    async with async_session_maker() as session:
        yield session
        