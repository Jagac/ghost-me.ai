from auth import AuthHandler
from database import AsyncSession, get_db
from database.models import UserModel
from emailwrapper import EmailRequestHandler
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse
from types import ResetPasswordSchema

router = APIRouter(prefix="/users", tags=["user"])
auth_service = AuthHandler()

email_service = EmailRequestHandler(
    email_service_url="http://emailservice:8000/v1/email"
)


@router.post("/forgot-password")
async def forget_password(
    background_tasks: BackgroundTasks,
    email: str = Depends(auth_service.get_current_user),
):
    new_token = await auth_service.create_access_token(data={"sub": email})

    background_tasks.add_task(
        email_service.create_and_push_message,
        address=email,
        subject="password reset",
        message=f"host {new_token}",
    )

    return ORJSONResponse(
        content={"message": "Email has been sent"}, status_code=status.HTTP_200_OK
    )


@router.post("/reset-password")
async def reset_password(rfp: ResetPasswordSchema, db: AsyncSession = Depends(get_db)):

    info = await auth_service.get_current_user(token=rfp.secret_token, db=db)

    if info is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid Password Reset Payload or Reset Link Expired",
        )

    if rfp.new_password != rfp.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password are not the same.",
        )

    hashed_password = await auth_service.hash_password(rfp.new_password)
    user = await UserModel.get_user(db, email=rfp.email)
    user.password = hashed_password
    await db.commit()
    return ORJSONResponse(
        content={"message": "Password reset successfully"},
        status_code=status.HTTP_200_OK,
    )
