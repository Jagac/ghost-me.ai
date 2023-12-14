import asyncio
from datetime import timedelta

import auth
import database
import models
import rabbitmq
import schemas
from fastapi import Depends, FastAPI, File, HTTPException, status
import logging

app = FastAPI()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# connect to rabbitmq on startup and initialize tables
async def startup_event():
    logging.info("Startup successful")
    app.rabbitmq_connection = await rabbitmq.create_rabbitmq_connection()
    await database.init_tables()


app.add_event_handler("startup", startup_event)


# health check
@app.get("/")
async def main():
    return {"server": "works"}


@app.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def create_upload_file(
    job_desc: str,
    current_user: str = Depends(auth.get_current_user),
    file: bytes = File(...),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    logging.info("Pushing to rabbitmq")
    asyncio.create_task(
        rabbitmq.publish_message(file, job_desc, current_user, app.rabbitmq_connection)
    )

    return {"message": "File uploaded successfully"}


@app.post("/users/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: schemas.UserCreate, db: database.AsyncSession = Depends(database.get_db)
):
    hashed_password = await auth.hash_password_async(user_data.password)

    new_user = models.User(username=user_data.username, password=hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logging.info(f"User {user_data.username} registered")

    return {"message": "User created successfully"}


@app.post("/users/login", status_code=status.HTTP_201_CREATED)
async def login_user(
    user_data: schemas.UserCreate, db: database.AsyncSession = Depends(database.get_db)
):
    user = await db.execute(
        models.User.__table__.select().where(models.User.username == user_data.username)
    )
    user_row = user.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    is_password_valid = await auth.verify_password_async(
        user_data.password, user_row.password
    )
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Password not found"
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await auth.create_access_token(
        data={"sub": user_row.username}, expires_delta=access_token_expires
    )
    logging.info(f"User {user_data.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}
