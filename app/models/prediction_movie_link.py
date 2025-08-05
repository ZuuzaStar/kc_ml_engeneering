from sqlmodel import SQLModel, Field
from typing import Optional


class PredictionMovieLink(SQLModel, table=True):
    """
    Таблица отношений "многие ко многим" между Prediction и Movie.
    """
    prediction_id: Optional[int] = Field(
        foreign_key="prediction.id", 
        primary_key=True
    )
    movie_id: Optional[int] = Field(
        foreign_key="movie.id", 
        primary_key=True
    )