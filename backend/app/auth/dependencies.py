import secrets
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.config import settings
from backend.app.security.jwt_handler import decode_access_token
from backend.app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    query = select(User).where(User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user

async def require_volunteer_token(
    x_volunteer_token: Optional[str] = Header(default=None),
) -> str:
    if not x_volunteer_token or not secrets.compare_digest(
        x_volunteer_token, settings.VOLUNTEER_REGISTRATION_TOKEN
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid volunteer token")
    return x_volunteer_token

async def get_user_or_volunteer(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    x_volunteer_token: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Allow either a normal user JWT or the worker service token."""
    if x_volunteer_token and secrets.compare_digest(
        x_volunteer_token, settings.VOLUNTEER_REGISTRATION_TOKEN
    ):
        return None
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    payload = decode_access_token(token)
    if not payload or payload.get("sub") is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = (await db.execute(select(User).where(User.id == int(payload["sub"])))).scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return user
