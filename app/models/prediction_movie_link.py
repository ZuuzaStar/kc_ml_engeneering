from sqlmodel import SQLModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.prediction import Prediction
    from models.movie import Movie


class PredictionMovieLink(SQLModel, table=True):
    """
    Таблица отношений "многие ко многим" между Prediction и Movie.

    Attributes:
        prediction_id (int): ID предсказания
        movie_id (int): ID фильма
    """
    prediction_id: int = Field(
        foreign_key="prediction.id", 
        primary_key=True
    )
    movie_id: int = Field(
        foreign_key="movie.id", 
        primary_key=True
    )