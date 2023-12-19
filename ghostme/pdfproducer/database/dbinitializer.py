from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    """
    Database class used to interact with postgres
    input is a connection string
    expects an async driver
    e.g. postgresql+asyncpg://username:password@host/dbname
    """

    def __init__(self, connection_string: str):
        self.engine = create_async_engine(connection_string, echo=True)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize_tables(self) -> None:
        """
        Creates the tables (usually used on initial boot up)
        Returns: None

        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        """
        Creates an async database session
        Returns: AsyncSession

        """

        db = self.async_session()
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()
