from dependencies import get_current_user
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status
)
from schemas.items import (
    Item, 
    ItemCreate, 
    ItemResponse, 
    ItemUpdate
)


router = APIRouter(tags=["Items"])

db_items = {
    1: {"id": 1, "name": "MacBook", "description": "Mini", "owner_id": 3},
    2: {"id": 2, "name": "IPhone", "description": "X", "owner_id": 2},
    3: {"id": 3, "name": "Samsung Phone", "description": "Galaxy S20", "owner_id": 5},
    4: {"id": 4, "name": "NoteBook", "description": "Asus", "owner_id": 1},
    5: {"id": 5, "name": "TV", "description": "Xiaomi", "owner_id": 1},
    6: {"id": 6, "name": "IPhone", "description": "17", "owner_id": 3},
    7: {"id": 7, "name": "TV", "description": "Samsung", "owner_id": 2},
    8: {"id": 8, "name": "Samsung Phone", "description": "Galaxy S24", "owner_id": 5},
    9: {"id": 9, "name": "NoteBook", "description": "Xiaomi", "owner_id": 4},
    10: {"id": 10, "name": "IPhone", "description": "17 Pro", "owner_id": 3}
}


@router.get("/items")
async def get_items(
    user = Depends(get_current_user)
):
    if user.role == "superadmin" or user.role == "admin":
        return db_items
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough rights"
    )


@router.get("/my_items")
async def get_my_items(
    user = Depends(get_current_user)
):
    return {id: Item(**db_items[id]) for id in db_items if db_items[id]["owner_id"] == user.id}


@router.get("/item/{item_id}")
async def get_item(
    item_id: int,
    user = Depends(get_current_user)
):
    item = db_items.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    if item["owner_id"] != user.id and user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough rights"
        )
    return ItemResponse(**item)


@router.post("/add_item")
async def add_item(
    item: ItemCreate,
    user = Depends(get_current_user)
):
    new_item = Item(
        id=len(db_items)+1,
        name=item.name,
        description=item.description,
        owner_id=user.id
    )
    db_items[new_item.id] = new_item.model_dump()
    return new_item


@router.patch("/update_item/{item_id}")
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    user = Depends(get_current_user)
):
    item = db_items.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    if item["owner_id"] != user.id and user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough rights"
        )
    if item_data.name:
        item["name"] = item_data.name
    if item_data.description:
        item["description"] = item_data.description
        
    db_items[item_id] = item 
    return ItemResponse(**item)


@router.delete("/delete_item/{item_id}")
async def delete_item(
    item_id: int,
    user = Depends(get_current_user)
):
    item = db_items.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    if item["owner_id"] != user.id and user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough rights"
        )
    del db_items[item_id]
    return {"message": f"Successfully deletem item with {item_id=}", 
            "items": {id: db_items[id] for id in range(1, len(db_items)+1) if db_items[id]["owner_id"] == user.id}}