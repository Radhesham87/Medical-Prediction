"""Pydantic v2 schemas for users and authentication."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    mobile: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=6, max_length=128)
    confirm_password: str
    college: str = ""
    city: str = ""
    state: str = ""

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    mobile: str
    college: str
    city: str
    state: str
    role: str
    status: str
    is_active: bool
    registration_date: datetime
    last_login: Optional[datetime] = None
    prediction_count: int = 0
    active_device_count: int = 0
    modules: dict = {}
    usage: dict = {}


class ModuleStatsOut(BaseModel):
    key: str
    label: str
    users_with_access: int
    unique_users: int
    predictions: int
    todays_predictions: int
    downloads: int


class ModuleAccessIn(BaseModel):
    aiims: bool = False
    all_india: bool = False
    maharashtra: bool = False
    deemed: bool = False
    veterinary: bool = False


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_label: str
    browser: str
    os: str
    ip: str
    is_active: bool
    created_at: datetime
    last_seen_at: datetime


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


class AdminStats(BaseModel):
    todays_by_module: dict = {}
    total_users: int
    pending_users: int
    approved_users: int
    rejected_users: int
    prediction_count: int
    todays_predictions: int
    total_downloads: int
