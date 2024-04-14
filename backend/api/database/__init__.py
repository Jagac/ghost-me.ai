from .dbhandler import DatabaseSessionManager, AsyncSession

sessionmanager = DatabaseSessionManager()


async def get_db():
    async with sessionmanager.session() as session:
        yield session
