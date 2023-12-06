from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://jagac:123@db_postgres:5432/ghostmedb"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db = async_session()
    try:
        yield db
    finally:
        await db.close()


class Base(DeclarativeBase):
    pass
