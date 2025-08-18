from __future__ import annotations
from models.base_model import BaseModel
from sqlmodel import Field, Relationship
from typing import Optional, List, Any
from typing import TYPE_CHECKING
from models.prediction_movie_link import PredictionMovieLink
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import ARRAY, String, Column, Float
from datetime import datetime
from pgvector.sqlalchemy import Vector

if TYPE_CHECKING:
    from models.prediction import Prediction


class Movie(BaseModel, table=True):
    """
    Класс для представления фильма, который модель может использовать для рекомендации.

    Attributes:
        title (str): Название фильма
        description (str): Описание фильма
        year (int): Год выхода фильма
        genres (str): Жанры фильма
        embedding (Vector(384)): Вектор эмбединга фильма длинной 384
    """

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=10, max_length=1000, unique=True)
    year: int = Field(ge=1888, le=datetime.now().year + 10)
    genres: List[str] = Field(sa_column=Column(ARRAY(String), nullable=False))
    embedding: Any = Field(sa_column=Column(Vector(384)))

    # Relationships
    predictions: Mapped[List["Prediction"]] = Relationship(
        sa_relationship=relationship(
            secondary=lambda: PredictionMovieLink.__table__, back_populates="movies"
        ),
        link_model=PredictionMovieLink,
    )

