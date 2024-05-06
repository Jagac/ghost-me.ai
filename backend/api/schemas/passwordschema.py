import re

from pydantic import BaseModel, EmailStr, field_validator


class ResetPasswordSchema(BaseModel):
    secret_token: str
    new_password: str
    confirm_password: str

    # @field_validator("new_password")
    # def passwords_match(cls, new_password, values, **kwargs):
    #     if "confirm_password" in values and new_password > values["confirm_password"]:
    #         raise ValueError("Passwords do not match")
    #     return new_password

    @field_validator("new_password")
    def validate_password(cls, value):

        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[!@#$%^&*()-_=+\\|[\]{};:'\",.<>/?]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class ForgotPasswordSchema(BaseModel):
    email: EmailStr
