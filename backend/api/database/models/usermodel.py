from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import  NoResultFound
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ..dbhandler import AsyncSession, Base


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    uploads = relationship(
        "UploadModel", back_populates="user", cascade="all, delete-orphan"
    )

    @classmethod
    async def add_user(cls, db: AsyncSession, **kwargs) -> None:
        transaction = cls(**kwargs)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

    @classmethod
    async def get_user(cls, db: AsyncSession, email: str) -> Optional["UserModel"]:
        try:
            query = select(cls).filter(cls.email == email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
        except NoResultFound:
            return None
        return user

    @classmethod
    async def get_user_password(cls, db: AsyncSession, email: str) -> Optional[str]:
        try:
            query = select(cls.password).filter(cls.email == email)
            hashed_password = await db.scalar(query)
            return hashed_password

        except NoResultFound:
            return None

    @classmethod
    async def get_uploads(cls, db: AsyncSession, email: str) -> Optional["UserModel"]:
        result = await db.execute(
            select(UserModel)
            .options(selectinload(UserModel.uploads))
            .filter(UserModel.email == email)
        )
        user = result.scalar()

        return user

    @classmethod
    async def delete_data(cls, db: AsyncSession, email: str) -> None:
        query = delete(cls).where(cls.email == email)
        result = await db.execute(query)

        if result.rowcount >= 0:
            await db.commit()
