"""Pytest fixtures for testing."""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Scenario, Rate
from app.services import session_service


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Allow the user IDs used across tests
    # (start_session checks a hardcoded allowlist; unlisted IDs get 403)
    saved_allowlist = session_service.ALLOWED_USER_IDS
    session_service.ALLOWED_USER_IDS = saved_allowlist | {
        "gap_trader", "history_trader", "multiuser", "testuser",
        "trader1", "trader2", "trader3", "trader4", "trader5",
        "trader6", "trader7",
    }

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    session_service.ALLOWED_USER_IDS = saved_allowlist


@pytest_asyncio.fixture
async def sample_scenario(test_session: AsyncSession) -> Scenario:
    """Create a sample scenario for testing."""
    scenario = Scenario(
        name="TEST_SCENARIO",
        start_datetime=datetime(2016, 1, 4),
        end_datetime=datetime(2016, 1, 8),
        time_interval_seconds=86400,
        game_type="ANY",
        initial_balance=1000000,
    )
    test_session.add(scenario)
    await test_session.commit()
    await test_session.refresh(scenario)
    return scenario


@pytest_asyncio.fixture
async def sample_rates(test_session: AsyncSession) -> list[Rate]:
    """Create sample exchange rates for testing."""
    rates = []
    for date in [datetime(2016, 1, 4), datetime(2016, 1, 5), datetime(2016, 1, 6)]:
        for currency, rate_value in [
            ("USD", Decimal("118.25")),
            ("EUR", Decimal("128.50")),
            ("GBP", Decimal("173.25")),
        ]:
            rate = Rate(
                currency=currency,
                timestamp=date,
                rate_to_jpy=rate_value,
            )
            test_session.add(rate)
            rates.append(rate)

    await test_session.commit()
    return rates
