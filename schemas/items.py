from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    description: str
   
    
class ItemResponse(ItemCreate):
    id: int
    

class Item(ItemCreate):
    id: int
    owner_id: int 
    

class ItemUpdate(BaseModel):
    name: str | None = None 
    description: str | None = None
    