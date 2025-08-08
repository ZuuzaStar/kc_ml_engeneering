from __future__ import annotations
from models.base_model import BaseModel
from sqlmodel import Field, Relationship
from typing import Optional, List
from typing import TYPE_CHECKING
from models.prediction_movie_link import PredictionMovieLink
from sqlalchemy.orm import Mapped, relationship

if TYPE_CHECKING:
    from models.prediction import Prediction


class Movie(BaseModel, table=True):
    """
    Класс для представления фильма, который модель может использовать для рекомендации.

    Attributes:
        title (str): Название фильма
        description (str): Описание фильма
        cover_image_url (str): URL обложки фильма

    Relationships:
        predictions (List["Prediction"]): Список предсказаний, где рекомендовался этот фильм
    """

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=10, max_length=1000)
    cover_image_url: str = Field(max_length=500)
    predictions: Mapped[List["Prediction"]] = Relationship(
        sa_relationship=relationship(
            secondary=lambda: PredictionMovieLink.__table__, back_populates="movie"
        ),
        link_model=PredictionMovieLink,
    )

