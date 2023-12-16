import asyncio
from datetime import timedelta

from database.dbinitializer import AsyncSession, Database
from database.models import UserModel
from fastapi import Depends, FastAPI, File, HTTPException, status
from schemas.userschema import UserSchema
from services import config
from services.auth import AuthService
from services.rabbitmq import RabbitMQService

app = FastAPI()
auth_service = AuthService()
rabbitmq_service = RabbitMQService(
    connection_url=(), exchange_name=(), queue_name=(), routing_key=()
)
database_service = Database(connection_string=())


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


@app.post("ghostmev1/documents", status_code=status.HTTP_202_ACCEPTED)
async def create_upload_file(
    job_desc: str,
    current_user: str = Depends(auth_service.get_current_user),
    file: bytes = File(...),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    config.logging.info("Pushing to rabbitmq")
    asyncio.create_task(
        rabbitmq_service.publish_message(
            file, job_desc, current_user, app.rabbitmq_connection
        )
    )

    return {"message": "Data uploaded successfully"}


@app.post("ghostmev1/users/register", status_code=status.HTTP_201_CREATED)
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


@app.post("ghostmev1/users/login", status_code=status.HTTP_201_CREATED)
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

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await auth_service.create_access_token(
        data={"sub": user_row.username}, expires_delta=access_token_expires
    )
    config.logging.info(f"User {user_data.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}
