from __future__ import annotations
from sqlmodel import Field, Relationship
from typing import List, TYPE_CHECKING, Any
from pydantic import field_serializer
from models.prediction_movie_link import PredictionMovieLink
from models.base_model import BaseModel
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector

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
        movies (Mapped[List["Movie"]]): Связь с фильмами из предсказания
    """

    user_id: int = Field(foreign_key="user.id", index=True)
    input_text: str = Field(min_length=10, max_length=2000)
    embedding: Any = Field(sa_column=Column(Vector(384)))
    cost: float = Field(default=0.0)
    
    # Relationships
    user: Mapped["User"] = Relationship(
        sa_relationship=relationship(back_populates="predictions")
    )
    movies: Mapped[List["Movie"]] = Relationship(  # Исправлено имя поля
        sa_relationship=relationship(
            secondary=lambda: PredictionMovieLink.__table__,
            back_populates="predictions",
        ),
        link_model=PredictionMovieLink,
    )

    @field_serializer("embedding")
    def serialize_embedding(self, embedding):  # type: ignore[no-redef]
        """Сериализует поле embedding для JSON"""
        try:
            return embedding.tolist()  # numpy ndarray -> list
        except Exception:
            return embedding
