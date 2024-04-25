import os
from contextlib import asynccontextmanager

from database import sessionmanager
from fastapi import FastAPI
from routes import upload_router, user_router


def init_app(init_db=True) -> "FastAPI":
    db_conn_string = os.getenv("DB_CONN_STRING")

    lifespan = None

    if init_db:
        sessionmanager.init(db_conn_string)

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await sessionmanager.create_all()
            yield
            if sessionmanager._engine is not None:
                await sessionmanager.close()

    server = FastAPI(title="FastAPI server", lifespan=lifespan, docs_url="/api/docs")

    server.include_router(user_router, prefix="/api", tags=["user"])
    server.include_router(upload_router, prefix="/api", tags=["uploads"])

    return server


app = init_app()
f = open("static/ascii-art.txt", "r")
ascii_art = f.read()
print(ascii_art)
f.close()
