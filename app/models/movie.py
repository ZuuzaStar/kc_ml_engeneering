from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.prediction import Prediction


class Movie(SQLModel, table=True):
    """
    Класс для представления фильма, который модель может использовать для рекомендации.
    
    Attributes:
        id (int): Уникальный идентификатор фильма
        title (str): Название фильма
        description (str): Описание фильма
        cover_image_url (str): URL изображения обложки фильма
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=10, max_length=1000)
    cover_image_url: str = Field(max_length=500)

    # Relationships
    predictions: List["Prediction"] = Relationship(back_populates="movies")
