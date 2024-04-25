from pydantic import BaseModel


class UploadSchema(BaseModel):
    pdf_resume: str
    job_description: str
