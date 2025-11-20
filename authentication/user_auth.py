from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import User
from schemas import UserRegister
from authentication.auth_utils import hash_password



router = APIRouter(tags=["JWT"])



@router.post("/register")
async def register(user: UserRegister, db: AsyncSession = Depends(get_session)):
    user_exist = await db.execute(select(User).where(User.email == user.email))
    if user_exist.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already created"
        )
        
    db_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role="user"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return {"message": f"Hello, {user.username}!",
            "db_user": db_user}
