import secrets

from db.database import get_session
from db.models import User
from dependencies import get_current_user
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    Request, 
    Response, 
    status
)
from schemas.users import (
    UserLogin,
    UserRegister,
    UserUpdate
)
from security import (
    create_access_token,
    hash_password, 
    verify_password,
    EXPIRE_ACCESS_TOKEN_MINUTES,
    verify_token
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(tags=["Authenticate"], prefix="/user")


@router.post("/register")
async def register(
    user: UserRegister,
    db: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    user_exist = await db.execute(select(User).where(User.email == user.email))
    if user_exist.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )
        
    if not secrets.compare_digest(user.password, user.confirm_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords must be the same"
        )
    db_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
    )
    db.add(db_user)
    await db.commit()
    
    return {"message": f"Hello, {user.username}!"}


@router.post("/login")
async def login(
    user: UserLogin, 
    response: Response, 
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    existing_token =  request.cookies.get("access_token")
    if existing_token:
        try:
            payload = verify_token(existing_token)
            if payload:
                result = await db.execute(select(User).where(User.email == payload.get("sub")))
                db_user = result.scalar_one_or_none()
                if db_user and db_user.is_active:
                    return {"message": "You are already logged in"}
        except Exception:
            response.delete_cookie(
                key="access_token",
                httponly=True,
                secure=True
            )
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
    
    payload = {"sub": db_user.email}
    token = create_access_token(payload)
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
    return UserUpdate(
        new_username=update_data.new_username,
        new_email=update_data.new_email,
    )
    
    
@router.post("/logout")
async def logout_user(
    response: Response,
    request: Request
) -> dict[str, str]:
    if not request.cookies.get("access_token"):
        return {"message": "You are not authenticated"}
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True
    )
    return {"message": "Logout successfully!"}
  
    
@router.delete("/delete")
async def delete_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if current_user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are a superadmin and cannot be deactivated"
        )
    current_user.is_active = False
    response.delete_cookie(key="access_token")
    await db.commit()
    return {"message": "Delete successfully!"}
    