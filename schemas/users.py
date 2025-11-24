from pydantic import (
    BaseModel, 
    ConfigDict, 
    EmailStr
)
    

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    new_username: str | None = None 
    new_email: str | None = None
    
    model_config = ConfigDict(from_attributes=True)