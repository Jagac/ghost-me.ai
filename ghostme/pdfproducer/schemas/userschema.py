from pydantic import BaseModel


class UserSchema(BaseModel):
    """
    Making sure these are strings
    """

    username: str
    password: str


class UserResponseSchema(BaseModel):
    pdf_resume: str
    job_description: str
