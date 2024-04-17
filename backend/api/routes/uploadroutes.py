import base64
import os
from typing import Optional

from auth import AuthHandler
from database import AsyncSession, get_db
from database.models import UploadModel, UserModel
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import ORJSONResponse
from rabbitmq import QueueHandler
from schemas import UploadSchema
from sqlalchemy.exc import SQLAlchemyError
import os


router = APIRouter(prefix="/users", tags=["uploads"])

mq_conn_string = os.getenv("mq_conn_string")
auth_service = AuthHandler()
rabbitmq_service = QueueHandler(
    connection_url=mq_conn_string,
    exchange_name="upload_exchange",
    queue_name="upload_queue",
    routing_key="resume_pdf",
)


@router.post(
    "/uploads",
    status_code=status.HTTP_202_ACCEPTED,
    response_class=ORJSONResponse,
)
async def create_upload_file(
    background_tasks: BackgroundTasks,
    job_desc: str = Form(...),
    current_user: str = Depends(auth_service.get_current_user),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):

    try:
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No file provided"
            )

        if not file.content_type or not file.content_type.startswith("application/pdf"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded file is not a PDF",
            )

        pdf_content = file.file.read()

        await UploadModel.add_upload(
            db=db,
            email=current_user,
            pdf_resume=pdf_content,
            job_description=job_desc,
        )

        background_tasks.add_task(
            rabbitmq_service.publish_message,
            file_content=pdf_content,
            job_desc=job_desc,
            username=current_user,
            connection=await rabbitmq_service.create_connection(),
        )

        return {"message": "Data uploaded successfully"}

    except Exception as e:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": e},
        )

    finally:
        file.file.close()


@router.get(
    "/uploads",
    response_model=list[UploadSchema],
    response_class=ORJSONResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_uploads(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(auth_service.get_current_user),
    skip: Optional[int] = 0,
    limit: Optional[int] = 10,
):
    try:
        uploads = await UploadModel.get_uploads(db, email=current_user)
        if not uploads:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No uploads found"
            )

        processed_uploads = []
        for upload in uploads:
            pdf_resume_base64 = base64.b64encode(upload.pdf_resume).decode()
            processed_uploads.append(
                {
                    "pdf_resume": pdf_resume_base64,
                    "job_description": upload.job_description,
                }
            )

        return processed_uploads

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )