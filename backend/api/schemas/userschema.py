import re

from pydantic import BaseModel, EmailStr, field_validator


class UserSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    def validate_email(cls, value):

        if "@" not in value:
            raise ValueError("Invalid email format")
        return value

    @field_validator("password")
    def validate_password(cls, value):

        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[!@#$%^&*()-_=+\\|[\]{};:'\",.<>/?]", value):
            raise ValueError("Password must contain at least one special character")
        return value
