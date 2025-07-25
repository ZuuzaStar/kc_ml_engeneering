from dataclasses import dataclass


@dataclass
class Movie:
    """
    Класс для представления фильма, который модель может использовать для рекомендации.
    
    Attributes:
        id (int): Уникальный идентификатор фильма
        title (str): Название фильма
        description (str): Описание фильма
        cover_image_url (str): URL изображения обложки фильма
    """
    id: int
    title: str
    description: str
    cover_image_url: str

    def __post_init__(self):
        self._validate_title()
        self._validate_description()

    def _validate_title(self):
        if len(self.title) < 1:
            raise ValueError("Название фильма должно быть не короче одного символа")

    def _validate_description(self):
        if len(self.description) < 10:
            raise ValueError("Описание фильма не должно быть короче 10 символов")
        
    def change_title(self, new_title: str):
        """Возможность исправлять ошибки в названии"""
        self.title = new_title
    
    def change_description(self, new_description: str):
        """Возможность исправлять ошибки в описании"""
        self.description = new_description