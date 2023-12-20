import asyncio
import base64
import os
from typing import Optional

from fastapi.responses import ORJSONResponse
from fastapi import Depends, FastAPI, File, HTTPException, status, BackgroundTasks
from sqlalchemy import delete, select

from database.dbinitializer import AsyncSession, Database
from database.models import UserModel, Ghost
from schemas.userschema import UserSchema, UserResponseSchema
from services import config
from services.auth import AuthService
from services.rabbitmq import RabbitMQService

db_conn_string = os.getenv("db_conn_string")
connection_url = os.getenv("connection_url")
# db_conn_string = "postgresql+asyncpg://jagac:123@db_postgres/ghostmedb"
# connection_url = "amqp://guest:guest@rabbitmq:5672/"

app = FastAPI()
auth_service = AuthService()
rabbitmq_service = RabbitMQService(
    connection_url=connection_url,
    exchange_name="upload_exchange",
    queue_name="upload_queue",
    routing_key="resume_pdf",
)
database_service = Database(connection_string=db_conn_string)


# connect to rabbitmq on startup and initialize tables
async def startup_event():
    config.logging.info("Startup successful")
    await database_service.initialize_tables()
    app.rabbitmq_connection = await rabbitmq_service.create_connection()
    f = open("ascii-art.txt", "r")
    ascii_art = f.read()
    print(ascii_art)
    f.close()


app.add_event_handler("startup", startup_event)


# health check
@app.get("/")
async def main():
    return {"server": "is working"}


@app.post(
    "/ghostmev1/users/register",
    status_code=status.HTTP_201_CREATED,
    response_class=ORJSONResponse,
)
async def create_user(
    user_data: UserSchema,
    db: AsyncSession = Depends(database_service.get_session),
    api_key: str = Depends(auth_service.validate_api_key),
):
    hashed_password = await auth_service.hash_password(user_data.password)

    new_user = UserModel(username=user_data.username, password=hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    config.logging.info(f"api_key working {api_key}")
    config.logging.info(f"User {user_data.username} registered")

    return {"message": "User created successfully"}


@app.post(
    "/ghostmev1/users/login",
    status_code=status.HTTP_201_CREATED,
    response_class=ORJSONResponse,
)
async def login_user(
    user_data: UserSchema, db: AsyncSession = Depends(database_service.get_session)
):
    query = select(UserModel).where(UserModel.username == user_data.username)
    user = await db.execute(query)
    user = user.scalar()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    is_password_valid = await auth_service.verify_password(
        user_data.password, user.password
    )
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Password not found"
        )

    access_token = await auth_service.create_access_token(data={"sub": user.username})
    config.logging.info(f"User {user_data.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(
    "/ghostmev1/uploads",
    status_code=status.HTTP_202_ACCEPTED,
    response_class=ORJSONResponse,
)
async def create_upload_file(
    background_tasks: BackgroundTasks,
    job_desc: str,
    current_user: str = Depends(auth_service.get_current_user),
    file: bytes = File(...),
    db: AsyncSession = Depends(database_service.get_session),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    new_ghosting_info = Ghost(
        username=current_user, pdf_resume=file, job_description=job_desc
    )

    db.add(new_ghosting_info)
    await db.commit()
    await db.refresh(new_ghosting_info)

    # are executed after the response is sent to the client
    background_tasks.add_task(
        rabbitmq_service.publish_message,
        file_content=file,
        job_desc=job_desc,
        username=current_user,
        connection=app.rabbitmq_connection,
    )

    return {"message": "Data uploaded successfully"}


@app.get(
    "/ghostmev1/users/uploads",
    response_model=list[UserResponseSchema],
    response_class=ORJSONResponse,
)
async def get_user_uploads(
    db: AsyncSession = Depends(database_service.get_session),
    current_user: str = Depends(auth_service.get_current_user),
    skip: Optional[int] = 0,
    limit: Optional[int] = 10,
):
    query = (
        select(UserModel)
        .join(Ghost)
        .filter(UserModel.username == current_user)
        .offset(skip)
        .limit(limit)
    )

    uploads = await db.execute(query)
    uploads = uploads.fetchall()

    if uploads:
        user_uploads = []
        for upload in uploads:
            pdf_resume_content_base64 = base64.b64encode(upload.pdf_resume).decode()

            user_upload = {
                "pdf_resume_content_base64": pdf_resume_content_base64,
                "job_description": upload.job_description,
            }
            user_uploads.append(UserResponseSchema(**user_upload))

        return user_uploads
    else:
        raise HTTPException(
            status_code=404, detail=f"No uploads found for user '{current_user}'"
        )


@app.delete("/ghostmev1/users/delete", status_code=status.HTTP_200_OK)
async def delete_user(
    db: AsyncSession = Depends(database_service.get_session),
    current_user: str = Depends(auth_service.get_current_user),
):
    query = delete(UserModel).where(UserModel.username == current_user)
    result = await db.execute(query)

    if result.rowcount > 0:
        await db.commit()
        return {"message": "User and associated data deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")
