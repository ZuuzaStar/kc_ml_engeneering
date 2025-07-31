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
        
    def change_title(self, new_title: str):
        """Возможность исправлять ошибки в названии"""
        if len(new_title) < 1:
            raise ValueError("Название фильма должно быть не короче одного символа")
        self.title = new_title
    
    def change_description(self, new_description: str):
        """Возможность исправлять ошибки в описании"""
        if len(new_description) < 10:
            raise ValueError("Описание фильма не должно быть короче 10 символов")
        self.description = new_description