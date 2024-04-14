from pydantic import BaseModel


class JWTSchema(BaseModel):
    access_token: str
    token_type: str
