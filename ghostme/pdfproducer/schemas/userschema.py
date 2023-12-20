from pydantic import BaseModel


class UserSchema(BaseModel):
    """
    Making sure these are strings
    """

    username: str
    password: str


class UserResponseSchema(BaseModel):
    pdf_resume_content_base64: str
    job_description: str
