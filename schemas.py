from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: Optional[str] = None # Opcional se for login com Google

class GoogleAuthRequest(BaseModel):
    credential_token: str # Token recebido do Google Sign-In no front

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TodoBase(BaseModel):
    text: str

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    completed: bool

class TodoResponse(TodoBase):
    id: int
    completed: bool
    class Config:
        from_attributes = True

class TreeHistoryResponse(BaseModel):
    id: int
    name: str
    level: int
    theme: str
    completed_at: str
    class Config:
        from_attributes = True

class InventoryItemResponse(BaseModel):
    id: int
    item_id: str
    quantity: int
    equipped: bool
    class Config:
        from_attributes = True

class DraftBase(BaseModel):
    template_id: str
    content: str

class DraftResponse(DraftBase):
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str]
    country: str
    xp: int
    level: int
    gems: int
    streak: int
    water_units: int
    skill_points: int
    tree_health: int
    tree_dead: bool
    mudas: int
    adubos: int
    essencias: int
    last_streak_date: Optional[str]
    last_activity_date: Optional[str]
    
    class Config:
        from_attributes = True

class RankUserResponse(BaseModel):
    username: str
    level: int
    xp: int
    country: str
    avatar_url: Optional[str]
    class Config:
        from_attributes = True
