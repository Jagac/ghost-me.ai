from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    AuthService class contains methods to add, verify, and retrieve users
    """

    api_key_header = APIKeyHeader(name="API-Key")

    def __init__(self):
        self.SECRET_KEY = (
            "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        )
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.API_KEY = "test-user-registration"

    @staticmethod
    async def hash_password(password: str) -> str:
        """
        hash password before inserting to db
        Args:
            password: str

        Returns: hashed password (str)

        """
        return pwd_context.hash(password)

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        verifying password so user can log in
        Args:
            plain_password: str
            hashed_password: str

        Returns: bool

        """
        return pwd_context.verify(plain_password, hashed_password)

    async def validate_api_key(self, api_key: str = Depends(api_key_header)):
        if api_key != self.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def create_access_token(self, data: dict) -> str:
        """
        Create JWT token
        Args:
            data: usually username

        Returns: JWT token (str)

        """
        to_encode = data.copy()
        expire = datetime.now() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> str:
        """
        Get current user
        Args:
            token: jwt token (str)

        Returns: username (str)

        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        return username
