import asyncio
from typing import Optional

from database.dbinitializer import AsyncSession, Database
from database.models import UserModel, Ghost
from fastapi import Depends, FastAPI, File, HTTPException, status
from schemas.userschema import UserSchema
from services import config
from services.auth import AuthService
from services.rabbitmq import RabbitMQService

db_conn_string = "postgresql+asyncpg://jagac:123@db_postgres/ghostmedb"
connection_url = "amqp://guest:guest@rabbitmq:5672/"

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


app.add_event_handler("startup", startup_event)


# health check
@app.get("/")
async def main():
    return {"server": "is working"}


@app.post("/ghostmev1/uploads", status_code=status.HTTP_202_ACCEPTED)
async def create_upload_file(
    job_desc: str,
    current_user: str = Depends(auth_service.get_current_user),
    file: bytes = File(...),
    db: AsyncSession = Depends(database_service.get_session),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    config.logging.info("Pushing to rabbitmq")
    await asyncio.create_task(
        rabbitmq_service.publish_message(
            file_content=file,
            job_desc=job_desc,
            username=current_user,
            connection=app.rabbitmq_connection,
        )
    )

    new_ghosting_info = Ghost(
        username=current_user, pdf_resume=file, job_description=job_desc
    )
    config.logging.info("Adding to pgs")
    db.add(new_ghosting_info)
    await db.commit()
    await db.refresh(new_ghosting_info)

    return {"message": "Data uploaded successfully"}


@app.post("/ghostmev1/users/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserSchema, db: AsyncSession = Depends(database_service.get_session)
):
    hashed_password = await auth_service.hash_password(user_data.password)

    new_user = UserModel(username=user_data.username, password=hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    config.logging.info(f"User {user_data.username} registered")

    return {"message": "User created successfully"}


@app.post("/ghostmev1/users/login", status_code=status.HTTP_201_CREATED)
async def login_user(
    user_data: UserSchema, db: AsyncSession = Depends(database_service.get_session)
):
    user_row = await db.execute(
        UserModel.__table__.select().where(UserModel.username == user_data.username)
    )
    user = user_row.fetchone()

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


@app.delete("/ghostmev1/users/delete")
async def delete_user(
    db: AsyncSession = Depends(database_service.get_session),
    current_user: str = Depends(auth_service.get_current_user),
):
    user_row = await db.execute(
        UserModel.__table__.select().where(UserModel.username == current_user)
    )
    user = user_row.fetchone()

    if user:
        await db.delete(user)
        await db.commit()
        return {"message": "User and associated data deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.get("/ghostmev1/users/uploads", response_model=list[dict])
async def get_user_uploads(
    db: AsyncSession = Depends(database_service.get_session),
    current_user: str = Depends(auth_service.get_current_user),
    skip: Optional[int] = 0,
    limit: Optional[int] = 10,
):
    uploads_query = (
        UserModel.__table__.join(Ghost.__table__)
        .select()
        .where(UserModel.username == current_user)
        .offset(skip)
        .limit(limit)
    )

    uploads = await db.execute(uploads_query)
    uploads = uploads.fetchall()

    if uploads:
        # Extract relevant information from the uploads
        user_uploads = [
            {
                "pdf_resume": upload.Ghost.pdf_resume,
                "job_description": upload.Ghost.job_description,
            }
            for upload in uploads
        ]
        return user_uploads
    else:
        raise HTTPException(
            status_code=404, detail=f"No uploads found for user '{current_user}'"
        )
