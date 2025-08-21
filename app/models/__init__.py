from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserSignupRequest(BaseModel):
    """Запрос на регистрацию пользователя"""
    email: EmailStr
    password: str
    is_admin: bool = False


class UserSigninRequest(BaseModel):
    """Запрос на вход пользователя"""
    email: EmailStr
    password: str


class UserEmailRequest(BaseModel):
    """Запрос с email пользователя"""
    email: EmailStr


class BalanceAdjustRequest(BaseModel):
    """Запрос на изменение баланса"""
    email: EmailStr
    amount: float


class MovieOut(BaseModel):
    """Выходная модель фильма"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    year: int
    genres: List[str]


class PredictionOut(BaseModel):
    """Выходная модель предсказания"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime
    user_id: int
    input_text: str
    cost: float
    movies: List[MovieOut] = []

