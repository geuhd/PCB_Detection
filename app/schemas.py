from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional
import uuid

class DetectBase(BaseModel):
    title: str
    path_original: str
    path: str
    published: bool = True

class  DetectCreate(DetectBase):
    id: int      # unique integer id
    created_at: datetime
    pass


class UserOut(BaseModel):
    id: int
    email:EmailStr
    created_at:datetime
    
    class Config:
        from_attributes=True 
        
class Detect(DetectBase):
    created_at:datetime
    class Config:
        from_attributes=True   
 
class DetectOut(BaseModel):
    post:Detect
    class Config:
        from_attributes=True 



class UserCreate(BaseModel):
    email: EmailStr
    password: str
class UserLogin(BaseModel):
    email: EmailStr
    password: str   

class Token(BaseModel):
    access_token:str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str]=None         
 