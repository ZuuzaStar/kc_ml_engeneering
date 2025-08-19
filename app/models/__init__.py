from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List
from datetime import datetime


class UserSignupRequest(BaseModel):
    email: str
    password: str


class UserSigninRequest(BaseModel):
    email: str
    password: str


class UserEmailRequest(BaseModel):
    email: str


class BalanceAdjustRequest(BaseModel):
    email: str
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

