from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import ForeignKey
from .dbinitializer import Base


class UserModel(Base):
    """
    Users table
    deletes data from the other table when user is deleted (cascade)
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    ghosts = relationship("Ghost", back_populates="user", cascade="all, delete-orphan")


class Ghost(Base):
    """
    This is where the pdfs and job descriptions go
    """

    __tablename__ = "ghost"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE")
    )
    pdf_resume: Mapped[bytes]
    job_description: Mapped[str]

    user = relationship("UserModel", back_populates="ghosts")
