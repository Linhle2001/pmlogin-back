from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str
    hwid: Optional[str] = None

class UserResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

class TokenResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

class ChangePassword(BaseModel):
    current_password: str
    password: str
    password_confirmation: str

# Tag schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Group schemas
class GroupBase(BaseModel):
    group_name: str

class GroupCreate(GroupBase):
    pass

class GroupResponse(BaseModel):
    id: int
    group_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Proxy schemas
class ProxyBase(BaseModel):
    host: str
    port: int
    username: Optional[str] = ""
    password: Optional[str] = ""
    type: Optional[str] = "http"
    name: Optional[str] = None

class ProxyCreate(ProxyBase):
    tags: Optional[List[str]] = ["Default"]

class ProxyUpdate(ProxyBase):
    tags: Optional[List[str]] = None

class ProxyResponse(BaseModel):
    id: int
    name: Optional[str]
    host: str
    port: int
    username: str
    password: str
    type: str
    status: str
    response_time: Optional[float]
    public_ip: Optional[str]
    location: Optional[str]
    fail_count: int
    last_tested: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]
    
    class Config:
        from_attributes = True

class ProxyTest(BaseModel):
    host: str
    port: int
    username: Optional[str] = ""
    password: Optional[str] = ""
    type: Optional[str] = "http"

class ProxyImport(BaseModel):
    proxy_text: str
    tags: Optional[List[str]] = ["Default"]

class ProxyStats(BaseModel):
    total: int
    live: int
    dead: int
    pending: int
    by_type: Dict[str, int]
    by_tag: Dict[str, int]
    avg_response_time: float
    last_tested: Optional[datetime]

# Profile schemas
class ProfileBase(BaseModel):
    name: str
    platform: Optional[str] = None
    note: Optional[str] = None
    proxy: Optional[str] = None

class ProfileCreate(ProfileBase):
    groups: Optional[List[str]] = []
    tags: Optional[List[str]] = []

class ProfileUpdate(ProfileBase):
    groups: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    shared_on_cloud: Optional[bool] = None

class ProfileResponse(BaseModel):
    id: int
    name: str
    platform: Optional[str]
    note: Optional[str]
    proxy: Optional[str]
    status: str
    shared_on_cloud: bool
    created_at: datetime
    updated_at: datetime
    last_started_at: Optional[datetime]
    groups: List[GroupResponse]
    tags: List[TagResponse]
    
    class Config:
        from_attributes = True

# Generic response schemas
class GenericResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]