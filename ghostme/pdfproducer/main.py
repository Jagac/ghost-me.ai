import asyncio
from datetime import timedelta

import auth
import database
import models
import schemas
from fastapi import Depends, FastAPI, File, HTTPException, status
from rabbitmq import MQ


async def startup_event():
    app.rabbitmq_connection = await MQ.create_rabbitmq_connection()


app = FastAPI()
app.add_event_handler("startup", startup_event)


@app.get("/")
async def main():
    return {"server": "works"}


@app.post("/uploadfile/", status_code=status.HTTP_202_ACCEPTED)
async def create_upload_file(
    current_user: str = Depends(auth.get_current_user),
    file: bytes = File(...),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    asyncio.create_task(MQ.publish_message(file, app.rabbitmq_connection))

    return {"message": "File uploaded successfully"}


@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: schemas.UserCreate, db: database.AsyncSession = Depends(database.get_db)
):
    hashed_password = await auth.hash_password_async(user_data.password)

    new_user = models.User(username=user_data.username, password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "User created successfully"}


@app.post("/login/")
async def login_user(
    user_data: schemas.UserCreate, db: database.AsyncSession = Depends(database.get_db)
):
    user = await db.execute(
        models.User.__table__.select().where(models.User.username == user_data.username)
    )
    user = user.fetchone()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    is_password_valid = await auth.verify_password_async(
        user_data.password, user.password
    )
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Password not found"
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
