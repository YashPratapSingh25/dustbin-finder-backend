import pytest
from httpx import ASGITransport, AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from core.db.db_config import Base
from core.dependencies import get_db_session
from main import app


engine = create_async_engine(
    settings.TEST_DB_URL,
    echo=False,
    pool_pre_ping=True,
)

TestSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db_session():
    async with TestSessionLocal() as session:
        async with session:

            yield session

            session.rollback()


@pytest_asyncio.fixture()
async def setup_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(setup_database):
    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db_session, None)

@pytest_asyncio.fixture
async def db_session(setup_database):
    async with TestSessionLocal() as session:
        async with session:
            yield session