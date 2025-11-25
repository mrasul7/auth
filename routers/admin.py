from db.database import get_session
from db.models import User
from dependencies import (
    get_current_admin, 
    get_current_superadmin
)
from fastapi import (
    APIRouter,
    Depends, 
    HTTPException,
    Query, 
    status
)
from pydantic import EmailStr
from schemas.users import (
    UserRegister,
    UserResponse
)
from security import hash_password
from sqlalchemy import (
    select,
    desc,
    asc, 
    update
)
from sqlalchemy.orm import load_only
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any


router = APIRouter(tags=["Admin"], prefix="/admin")


@router.post("", description="Create new admin user")
async def create_admin(
    user: UserRegister,
    db: AsyncSession = Depends(get_session),
    superadmin = Depends(get_current_superadmin),
) -> dict[str, str]:
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin with this email already exists"
        )
    db_admin = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role="admin"
    )
    
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    return {"message": f"Admin with email {db_admin.email} successfully created"}


@router.post(path="/role", description="You can either grant or revoke the admin role. Roles: admin, user")
async def change_role(
    email: EmailStr,
    new_role: str,
    db: AsyncSession = Depends(get_session),
    superadmin = Depends(get_current_superadmin)
) -> dict[str, Any]:
    if new_role not in ("admin", "user"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong role. The role must be either admin or user"
        )
    old_role_stmt = select(User).where(User.email == email)
    result = await db.execute(old_role_stmt)
    data_user = result.scalar_one_or_none()
    if not data_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with {email=} not found"
        )
    if data_user.role == new_role:
        return {"message": "The same role that the user has is transferred"}
    old_role = data_user.role
    
    update_stmt = (
        update(User)
        .where(User.email == email)
        .values(role=new_role)
    )
        
    await db.execute(update_stmt)
    await db.commit()
    
    updated_user_stmt = select(User).where(User.email == email)
    result = await db.execute(updated_user_stmt)
    updated_user = result.scalar_one()
    user_info = {
        "username": updated_user.username,
        "id": updated_user.id,
        "email": updated_user.email,
        "is_active": updated_user.is_active,
        "role": updated_user.role
    }
    
    return {"result": "Successfully",
            "user": user_info,
            "old_role": old_role,
            "new_role": updated_user.role}
    

@router.get("/users", description="Get users list with filtering and sorting", response_model=list[UserResponse])
async def get_all_users(
    limit: int = Query(None, ge=0),
    offset: int = Query(default=0, ge=0),
    is_active: bool = Query(None, description="True or False or nothing"),
    roles: str = Query(
        default=None, 
        description="Select the desired roles: admin, superadmin, user. Example: admin,user"
    ),
    sort_by: str = Query(
        default=None, 
        description='''You must specify the sorting field and, separated by a colon, how to sort(case does not matter).
                       Example:id:desc,username:ASC,is_active:DeSc'''),
    db: AsyncSession = Depends(get_session),
    admin = Depends(get_current_admin),
):
    query = select(User)
    try:
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        if is_active is True or is_active is False:
            query = query.where(User.is_active == is_active)
        if roles:
            query = query.where(User.role.in_(roles.split(","))) 
        
        if sort_by:
            sort_field = sort_by.split(",")
            for field in sort_field:
                field_name, sort_order = field.split(":")
                
                column = getattr(User, field_name.lower(), None)
                if column:
                    query = query.order_by(desc(column) if sort_order.lower() == "desc" else asc(column))
                    
        result = await db.execute(query)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filtering or sorting data was passed"
        )
    return result.scalars().all()

@router.patch("/users/status", description="Activate and deactivate one or more users")
async def activate_or_deactivate_users(
    active: bool = Query(..., description="True to activate, False to deactivate"),
    ids: str = Query(
        default=..., 
        description="Specify id separated by commas or a ranges using -. Example: 1,2,3 or 5-10,13-23"
    ),
    db: AsyncSession = Depends(get_session),
    user = Depends(get_current_admin),
) -> dict[str, str]:
    try:
        if "-" in ids:
            ranges = ids.split(",")
            current_ids = set()
            for r in ranges:
                mid = r.split("-")
                if len(mid) == 1:
                    id = int(mid[0])
                    current_ids.add(id)
                elif len(mid) == 2:
                    start, end = map(int, r.split("-"))
                    current_ids.update(set(range(start, end+1)))
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid data"
                    )
        else:
            current_ids = list(map(int, ids.split(",")))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred {e}"
        )
        
    if user.role == "superadmin":
        select_stmt = (
            select(User.id, User.username, User.email, User.is_active)
            .where(User.id.in_(current_ids), User.role != "superadmin")
        )
    else:
        select_stmt = (
            select(User.id, User.username, User.email, User.is_active)
            .where(User.id.in_(current_ids), User.role.not_in(["admin", "superadmin"]))
        )
        
    result = await db.execute(select_stmt)
    users_before = result.mappings().all()
    
    if user.role == "superadmin":
        update_stmt = (
            update(User)
            .where(User.id.in_(current_ids), User.role != "superadmin")
            .values(is_active=active)
        )
    else:
        result = await db.execute(select(User).where(User.role == "superadmin"))
        superadmin = result.scalar_one()
        if superadmin.id in current_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You cannot deactivate a user with the superadmin(id={superadmin.id}) role."
            )
        update_stmt = (
            update(User)
            .where(User.id.in_(current_ids), User.role.not_in(["admin", "superadmin"]))
            .values(is_active=active)
        )    
    await db.execute(update_stmt)
    await db.commit()
    
    info = []
    for user_data in users_before:
        info.append({
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "old_is_active": user_data["is_active"],
            "new_is_active": active
        })
    return {"result": "Successfully",
            "info": f"{info}"}

