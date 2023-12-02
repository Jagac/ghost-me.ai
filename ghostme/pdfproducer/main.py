import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from utils import MQProducer

app = FastAPI()
producer = MQProducer("resume_pdf")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key is None or api_key != "test":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key


@app.get("/")
async def main():
    return {"server": "works"}


@app.post("/trigger-scraper-task/")
async def scraper_task_trigger(api_key: str = "test"):
    try:
        api_key = "test"
        url = "http://scrapers:8000/trigger-task/{data}"
        headers = {"X-API-Key": api_key}

        response = httpx.post(url, headers=headers)

        if response.status_code == 200:
            return JSONResponse(
                content={"message": "Scraper task triggered successfully"}
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to trigger scraper task",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/uploadfile/")
async def create_upload_file(
    file: bytes = File(...), api_key: str = Depends(get_api_key)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if b"%PDF" not in file:
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")

    producer.publish(message=file, routing_key="resume_pdf")

    return {"status": "File uploaded successfully"}
