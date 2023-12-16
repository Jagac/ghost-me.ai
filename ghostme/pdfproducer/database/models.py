from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


from .dbinitializer import Base

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]


#     profiles = relationship('UserProfile', back_populates='user')

# class UserProfile(Base):
#     __tablename__ = "user_profiles"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     username = Column(String, ForeignKey('users.username'))
#     bytes_data = Column(Binary)
#     user = relationship('User', back_populates='profiles')
