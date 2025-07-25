from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from movie import Movie
from user import User

@dataclass
class Prediction:
    """
    Класс для представления списка рекомендаций фильмов.
    
    Attributes:
        id (int): Уникальный идентификатор рекомендации
        user (User): Пользователь, для которого предлагается рекомендация
        input_text (str): Промт пользователя
        results (List[Movie]): Список рекомендованных фильмов
        cost (float): Стоимость генерации рекомендаций
        timestamp (datetime): Время запроса от пользователя
        is_success (bool): Успешен ли запрос
        error_message (str): Текст ошибки, если предсказание не удалось. По умолчанию "".
    """
    id: int
    user: User
    input_text: str
    results: List[Movie] = field(default_factory=list)
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    is_success: bool = True
    error_code: int = 0

    def __post_init__(self) -> None:
        self._validate_input_text()

    def _validate_input_text(self) -> None:
        """Проверяет, что запрос удовлетворяет требованиям"""
        if len(self.input_text) < 10:
            raise ValueError("Запрос должен быть длинне 10 символов")