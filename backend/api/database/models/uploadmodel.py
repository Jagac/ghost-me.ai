from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from sqlalchemy import select
from .usermodel import UserModel
from ..dbhandler import AsyncSession, Base


class UploadModel(Base):
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(ForeignKey("users.email", ondelete="CASCADE"))
    pdf_resume: Mapped[bytes]
    job_description: Mapped[str]
    
    user = relationship("UserModel", back_populates="uploads")

    @classmethod
    async def add_upload(cls, db: AsyncSession, **kwargs) -> None:
        transaction = cls(**kwargs)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

    @classmethod
    async def get_uploads(cls, db: AsyncSession, email: str) -> Optional["UploadModel"]:
        result = await db.execute(
            select(UploadModel)
            .join(UploadModel.user)
            .options(joinedload(UploadModel.user))
            .filter(UserModel.email == email)
        )
        uploads = result.scalars().all()
        return uploads