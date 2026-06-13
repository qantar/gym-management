"""Pytest configuration and shared fixtures."""
import asyncio
import uuid
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.branch import Branch


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def seed_branch(db_session: AsyncSession) -> Branch:
    # Use unique code per test to avoid UNIQUE conflicts
    code = f"TST-{uuid.uuid4().hex[:6].upper()}"
    branch = Branch(name="Test Branch", code=code, city="Riyadh", capacity=100)
    db_session.add(branch)
    await db_session.flush()
    return branch


@pytest_asyncio.fixture
async def seed_admin(db_session: AsyncSession, seed_branch: Branch) -> User:
    # Use unique email per test
    email = f"admin_{uuid.uuid4().hex[:6]}@gymos.sa"
    user = User(
        email=email,
        full_name="Test Admin",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.SUPER_ADMIN,
        branch_id=seed_branch.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, seed_admin: User) -> dict:
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": seed_admin.email, "password": "Admin@123"},
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
