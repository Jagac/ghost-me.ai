import base64
import os
from typing import Annotated, Optional

from auth.authentication import AuthHandler
from database import AsyncSession, get_db
from database.models.usermodel import UserModel
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import ORJSONResponse
from schemas import UserSchema, JWTSchema
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/users", tags=["user"])

auth_service = AuthHandler()


@router.get("/")
def index(user: Annotated[str, Depends(auth_service.get_current_user)]):
    if user:
        print(user)
    return {"message": user}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_class=ORJSONResponse,
)
async def create_user(
    user_data: UserSchema,
    db: AsyncSession = Depends(get_db),
):
    try:
        validated_user_data = UserSchema(**user_data.model_dump())

        hashed_password = await auth_service.hash_password(user_data.password)
        await UserModel.add_user(db=db, email=user_data.email, password=hashed_password)

        return {"message": "User created successfully"}

    except IntegrityError as e:
        await db.rollback()
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": e},
        )

    except HTTPException as e:
        await db.rollback()
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": e},
        )


@router.post(
    "/login",
    status_code=status.HTTP_202_ACCEPTED,
    response_class=ORJSONResponse,
)
async def login_user(user_data: UserSchema, db: AsyncSession = Depends(get_db)):
    try:
        hashed_password = await UserModel.get_user_password(db, user_data.email)

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
            data={"sub": user_data.email}
        )

        return JWTSchema(access_token=access_token, token_type="bearer")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)


@router.delete("/delete", status_code=status.HTTP_200_OK, response_class=ORJSONResponse)
async def delete_user(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(auth_service.get_current_user),
):
    try:
        await UserModel.delete_data(db, email=current_user)

        return {"message": "User and associated data deleted successfully"}

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
