from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_is_sqlite = "sqlite" in settings.DATABASE_URL.lower()

# asyncpg-specific connect args only for PostgreSQL
_connect_args = {} if _is_sqlite else {
    "server_settings": {"jit": "off"},
    "command_timeout": 60,
}

# Pool settings — StaticPool for SQLite (thread-safe in-memory), NullPool not needed
_engine_kwargs: dict = {
    "echo": settings.DEBUG and settings.ENVIRONMENT == "development",
    "connect_args": _connect_args,
}

if not _is_sqlite:
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 40,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
