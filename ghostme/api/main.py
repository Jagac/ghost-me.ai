import base64
import os
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    status,
    BackgroundTasks,
    UploadFile,
)
from fastapi.responses import ORJSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm import selectinload

from database.dbinitializer import AsyncSession, Database
from database.models import UserModel, Ghost
from schemas.userschema import UserSchema, UserResponseSchema
from services.auth import AuthService
from services.rabbitmq import RabbitMQService

db_conn_string = os.getenv("db_conn_string")
connection_url = os.getenv("connection_url")
# db_conn_string = "postgresql+asyncpg://jagac:123@db_postgres/ghostmedb"
# connection_url = "amqp://guest:guest@rabbitmq:5672/"


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
    await database_service.initialize_tables()
    app.rabbitmq_connection = await rabbitmq_service.create_connection()
    f = open("ascii-art.txt", "r")
    ascii_art = f.read()
    print(ascii_art)
    f.close()


app.add_event_handler("startup", startup_event)


# health check
@app.get("/")
async def main():
    return {"server": "is working"}


@app.post(
    "/ghostmev1/users/register",
    status_code=status.HTTP_201_CREATED,
    response_class=ORJSONResponse,
)
async def create_user(
    user_data: UserSchema,
    db: AsyncSession = Depends(database_service.get_session),
    api_key: str = Depends(auth_service.validate_api_key),
):
    try:
        hashed_password = await auth_service.hash_password(user_data.password)

        new_user = UserModel(username=user_data.username, password=hashed_password)

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {"message": "User created successfully"}

    except IntegrityError as e:
        await db.rollback()
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Username already exists"},
        )

    except HTTPException as e:
        await db.rollback()
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@app.post(
    "/ghostmev1/users/login",
    status_code=status.HTTP_201_CREATED,
    response_class=ORJSONResponse,
)
async def login_user(
    user_data: UserSchema, db: AsyncSession = Depends(database_service.get_session)
):
    try:
        query = select(UserModel.password).filter(
            UserModel.username == user_data.username
        )
        hashed_password = await db.scalar(query)

        if hashed_password is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        is_password_valid = await auth_service.verify_password(
            user_data.password, hashed_password
        )

        if not is_password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
            )

        access_token = await auth_service.create_access_token(
            data={"sub": user_data.username}
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post(
    "/ghostmev1/uploads",
    status_code=status.HTTP_202_ACCEPTED,
    response_class=ORJSONResponse,
)
async def create_upload_file(
    background_tasks: BackgroundTasks,
    job_desc: str,
    current_user: str = Depends(auth_service.get_current_user),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database_service.get_session),
):
    try:
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No file provided"
            )

        if not file.content_type or not file.content_type.startswith("application/pdf"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded file is not a PDF",
            )

        new_ghosting_info = Ghost(
            username=current_user, pdf_resume=file.file.read(), job_description=job_desc
        )

        db.add(new_ghosting_info)
        await db.commit()
        await db.refresh(new_ghosting_info)

        background_tasks.add_task(
            rabbitmq_service.publish_message,
            file_content=file.file.read(),
            job_desc=job_desc,
            username=current_user,
            connection=app.rabbitmq_connection,
        )

        return {"message": "Data uploaded successfully"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )


@app.get(
    "/ghostmev1/users/uploads",
    response_model=list[UserResponseSchema],
)
async def get_user_uploads(
    db: AsyncSession = Depends(database_service.get_session),
    current_user: str = Depends(auth_service.get_current_user),
    skip: Optional[int] = 0,
    limit: Optional[int] = 10,
):
    try:
        result = await db.execute(
            select(UserModel)
            .options(selectinload(UserModel.ghosts))
            .filter(UserModel.username == current_user)
        )
        user = result.scalar()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        uploads = []
        for ghost in user.ghosts:
            pdf_resume_base64 = base64.b64encode(ghost.pdf_resume).decode()
            uploads.append(
                {
                    "pdf_resume": pdf_resume_base64,
                    "job_description": ghost.job_description,
                }
            )

        return uploads

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.delete("/ghostmev1/users/delete", status_code=status.HTTP_200_OK)
async def delete_user(
    db: AsyncSession = Depends(database_service.get_session),
    current_user: str = Depends(auth_service.get_current_user),
):
    try:
        query = delete(UserModel).where(UserModel.username == current_user)
        result = await db.execute(query)

        if result.rowcount > 0:
            await db.commit()
            return {"message": "User and associated data deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
