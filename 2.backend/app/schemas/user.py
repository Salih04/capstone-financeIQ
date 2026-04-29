from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    user_type: str = "individual"
    risk_level: str = "medium"
    investment_scope: float | None = None
    sector_focus: str | None = None
    is_active: bool = True
    failed_login_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserProfileSetup(BaseModel):
    user_type: str
    risk_level: str
    investment_scope: float | None = None
    sector_focus: str | None = None
