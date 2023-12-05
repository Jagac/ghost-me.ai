import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import aio_pika
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.security import (
    APIKeyHeader,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)

# from jose import JWTError, jwt
import asyncio
from rabbitmq_publisher import MQ


async def startup_event():
    app.rabbitmq_connection = await MQ.create_rabbitmq_connection()


app = FastAPI()
app.add_event_handler("startup", startup_event)


@app.get("/")
async def main():
    return {"server": "works"}


@app.post("/uploadfile/")
async def create_upload_file(
    file: bytes = File(...),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    asyncio.create_task(MQ.publish_message(file, app.rabbitmq_connection))

    return {"status": "File uploaded successfully"}
