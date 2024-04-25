from typing import Annotated

from auth.authentication import AuthHandler
from database import AsyncSession, get_db
from database.models.usermodel import UserModel
from emailwrapper import EmailRequestHandler
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse
from schemas import ForgotPasswordSchema, JWTSchema, ResetPasswordSchema, UserSchema
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

email_service = EmailRequestHandler(
    email_service_url="http://emailservice:8000/v1/email"
)
auth_service = AuthHandler()
router = APIRouter(prefix="/users", tags=["user"])


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


@router.post("/forgot-password")
async def forgot_password(
    user_email: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        db_email = await UserModel.get_user(db, email=user_email.email)
        if not db_email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email does not exist",
            )

        new_token = await auth_service.create_access_token(
            data={"sub": user_email.email}
        )

        background_tasks.add_task(
            email_service.create_and_push_message,
            user_email.email,
            "Password Reset",
            f"Hello, this is your token for password reset: {new_token}",
        )

        return ORJSONResponse(
            content={"message": "Email has been sent"}, status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/reset-password")
async def reset_password(
    passwor_reset_form: ResetPasswordSchema, db: AsyncSession = Depends(get_db)
):
    try:
        info = await auth_service.get_current_user(
            token=passwor_reset_form.secret_token, db=db
        )

        if info is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Password Reset Payload or Reset Link Expired",
            )

        if passwor_reset_form.new_password != passwor_reset_form.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirm password are not the same.",
            )

        hashed_password = await auth_service.hash_password(
            passwor_reset_form.new_password
        )
        user = await UserModel.get_user(db, email=info)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        user.password = hashed_password
        await db.commit()

        return ORJSONResponse(
            content={"message": "Password reset successfully"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
