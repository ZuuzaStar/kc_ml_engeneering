from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False


class UserSigninRequest(BaseModel):
    email: EmailStr
    password: str


class UserEmailRequest(BaseModel):
    email: EmailStr


class BalanceAdjustRequest(BaseModel):
    email: EmailStr
    amount: float


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    year: int
    genres: List[str]


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime
    user_id: int
    input_text: str
    cost: float
    movies: List[MovieOut] = []

