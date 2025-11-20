from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import user

from db.database import get_session
from db.models import User
from authentication.schemas import UserLogin, UserRegister, UserUpdate
from authentication.auth_utils import create_access_token, get_current_user, hash_password, verify_password, EXPIRE_ACCESS_TOKEN_MINUTES





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


@router.post("/login")
async def login(user: UserLogin, response: Response, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password"
        )
    
    if not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive"
        )
    

    token = create_access_token({"sub": db_user.email})
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=60*EXPIRE_ACCESS_TOKEN_MINUTES,
        secure=True,
        httponly=True
    )
    return {"message": f"Hello, {db_user.username}!"}
    
@router.patch("/update")
async def update_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_session)
) -> UserUpdate:
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
        
    await db.commit()
    await db.refresh(current_user)
    return UserUpdate(
        username=update_data.username,
        email=update_data.email
    )