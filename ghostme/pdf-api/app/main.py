import json
import logging
import os
import warnings
from secrets import token_hex

import aiofiles
import utils
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse
import base64
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()


@app.get("/")
async def main():
    content = """
    <body>
    <form action='/upload' enctype='multipart/form-data' method='post'>
    <input name='file' type='file'>
    <input type='submit'>
    </form>
    </body>
    """
    return HTMLResponse(content=content)


@app.post("/upload", response_class=HTMLResponse)
async def post_file(file: UploadFile = File(...)):
    file_extension = file.filename.split(".").pop()
    if file_extension == "pdf":
        try:
            file_name = token_hex(10)  # anonymize file name
            logging.info(f"received {file_name}")
            file_path = f"data/{file_name}.{file_extension}"  # save file

            contents = await file.read()
            async with aiofiles.open(f"{file_path}", "wb") as f:
                await f.write(contents)

        except Exception as error:
            logging.exception(error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="There was an error uploading the file",
            )

        finally:
            await file.close()

    async with aiofiles.open(f"{file_path}", "rb") as f:
        encoded_string = base64.b64encode(await f.read())

    prod = utils.MQProducer("resume_pdf")
    prod.publish(message=encoded_string, routing_key="resume_pdf")
    os.remove(file_path)

    content = """
    <html>
        <head>
            <title>Success</title>
        </head>
        <body>
            <h1>Upload Successful</h1>
        </body>
        
    </html>
    """
    return HTMLResponse(content=content, status_code=200)
