from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from models.prediction_movie_link import PredictionMovieLink
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from models.user import User
    from models.movie import Movie


class Prediction(SQLModel, table=True):
    """
    Класс для представления списка рекомендаций фильмов.
    
    Attributes:
        id (int): ID рекомендации
        user_id (int): ID пользователя, для которого предлагается рекомендация
        input_text (str): Промт пользователя
        cost (float): Стоимость генерации рекомендаций
        timestamp (datetime): Время запроса от пользователя
        user (User): Взаимосвязь с объектом User
        results (List[Movie]): Связь с фильмами из предсказания
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    input_text: str = Field(min_length=10, max_length=2000)
    cost: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = Relationship(back_populates="predictions")
    results: Mapped[List["Movie"]] = Relationship(
        back_populates="predictions",
        link_model=PredictionMovieLink
    )
