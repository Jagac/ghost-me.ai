from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import ForeignKey
from .dbinitializer import Base


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    ghosts = relationship("Ghost", back_populates="user")


class Ghost(Base):
    __tablename__ = "ghost"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(ForeignKey("users.username"))
    pdf_resume: Mapped[bytes]
    job_description: Mapped[str]

    user = relationship("UserModel", back_populates="ghosts")
