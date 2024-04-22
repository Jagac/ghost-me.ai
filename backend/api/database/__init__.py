from .dbhandler import AsyncSession, DatabaseSessionManager

sessionmanager = DatabaseSessionManager()


async def get_db():
    async with sessionmanager.session() as session:
        yield session
