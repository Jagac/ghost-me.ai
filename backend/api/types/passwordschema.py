from pydantic import BaseModel


class ResetPasswordSchema(BaseModel):
    secret_token: str
    new_password: str
    confirm_password: str
