from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = "sqlite+aiosqlite:///database.db"


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    url=DATABASE_URL
)

session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()