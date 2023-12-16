import asyncio
from datetime import timedelta

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
    return {"server": "works"}


@app.post("/ghostmev1/documents", status_code=status.HTTP_202_ACCEPTED)
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
            file, job_desc, current_user, app.rabbitmq_connection
        )
    )
    new_ghosting_info = Ghost(
        username=current_user, pdf_resume=file, job_description=job_desc
    )
    db.add(new_ghosting_info)
    await db.commit()
    await db.refresh(new_ghosting_info)

    return {"message": "Data uploaded successfully"}


@app.post("/ghostmev1/users/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserSchema, db: AsyncSession = Depends(database_service.get_session)
):
    hashed_password = await auth_service.hash_password_async(user_data.password)

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
    user = await db.execute(
        UserModel.__table__.select().where(UserModel.username == user_data.username)
    )
    user_row = user.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    is_password_valid = await auth_service.verify_password_async(
        user_data.password, user_row.password
    )
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Password not found"
        )

    access_token = await auth_service.create_access_token(
        data={"sub": user_row.username}
    )
    config.logging.info(f"User {user_data.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}
