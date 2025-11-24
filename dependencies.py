from db.database import get_session
from db.models import User
from fastapi import (
    Depends, 
    HTTPException, 
    Request, 
    status
)
from security import verify_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        payload = verify_token(token)
        email = payload["sub"]
        
        result = await db.execute(select(User).where(User.email == email))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return db_user
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid"
        )
        
        
async def get_current_admin(
    current_user = Depends(get_current_user)
):
    if not current_user.role == "admin" and not current_user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough rights"
        )
    return current_user


async def get_current_superadmin(
    current_user = Depends(get_current_user)
):
    if not current_user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough rights"
        )
    return current_user

