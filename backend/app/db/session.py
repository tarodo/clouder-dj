from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.settings import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
