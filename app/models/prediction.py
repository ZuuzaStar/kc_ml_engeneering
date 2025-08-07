from __future__ import annotations
from sqlmodel import Field, Relationship
from typing import  List, TYPE_CHECKING
from models.prediction_movie_link import PredictionMovieLink
from models.base_model import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.movie import Movie


class Prediction(BaseModel, table=True):
    """
    Класс для представления списка рекомендаций фильмов.
    
    Attributes:
        user_id (int): ID пользователя, для которого предлагается рекомендация
        input_text (str): Промт пользователя
        cost (float): Стоимость генерации рекомендаций
    
    Relationships:
        user (Mapped["User"]): Взаимосвязь с объектом User
        results (Mapped[List["Movie"]]): Связь с фильмами из предсказания
    """
    user_id: int = Field(foreign_key="user.id", index=True)
    input_text: str = Field(min_length=10, max_length=2000)
    cost: float = Field(default=0.0)
    user: "User" = Relationship(back_populates="predictions")
    results: List["Movie"] = Relationship(
        back_populates="predictions",
        link_model=PredictionMovieLink
    )
