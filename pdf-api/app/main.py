from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from secrets import token_hex
import os
from pyresparser import ResumeParser
import warnings
import aiofiles
import socket

warnings.filterwarnings("ignore")

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


async def _resume(file_path):
    parser = ResumeParser(file_path)
    data = parser.get_extracted_data()

    return data


@app.post("/upload")
async def post_file(file: UploadFile = File(...)):
    file_extension = file.filename.split(".").pop()
    if file_extension == "pdf":
        try:
            file_name = token_hex(10)  # anonymize file name
            file_path = f"data/{file_name}.{file_extension}"  # save file

            contents = await file.read()
            async with aiofiles.open(f"{file_path}", "wb") as f:
                await f.write(contents)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="There was an error uploading the file",
            )

        finally:
            await file.close()

    data = await _resume(file_path)
    os.remove(file_path)

    return {
        "successfully parsed": jsonable_encoder(data),
    }
