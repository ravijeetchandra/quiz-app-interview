from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings


def _build_async_url(url: str) -> str:
    if url.startswith("sqlite"):
        return url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    from urllib.parse import urlparse, urlencode, parse_qs
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    qs.pop("sslmode", None)
    return parsed._replace(query=urlencode(qs, doseq=True)).geturl()


engine = create_async_engine(_build_async_url(settings.database_url), echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from models import User, QuizSession, Question, UserAnswer, PasswordResetToken  # noqa
        await conn.run_sync(Base.metadata.create_all)
