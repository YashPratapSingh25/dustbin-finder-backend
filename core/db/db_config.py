from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.SHOW_DB_LOG,
    pool_pre_ping = True,
    pool_size = 5,
    max_overflow = 15,
    pool_timeout = 30,
    pool_recycle = 3600, 
    connect_args = {
        "timeout": 10,
        "command_timeout": 30
    }
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass