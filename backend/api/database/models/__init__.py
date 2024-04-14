from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .uploadmodel import UploadModel
from .usermodel import UserModel
