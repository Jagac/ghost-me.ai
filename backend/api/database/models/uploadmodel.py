from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
