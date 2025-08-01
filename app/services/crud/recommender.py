from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from models.movie import Movie
    from models.user import User


class MLModel(ABC):
    """
    Абстрактный класс для самой ML модели
    """
    @abstractmethod
    def predict(self, input_text: str) -> List[Movie]:
        pass

class MovieRecommender(MLModel):
    """
    Класс, который наследует модель, список фильмов в базе и имеет метод predict
    Attributes:
        movies (List[Movie]): Список объектов фильмов из которых модель будет рекомендовать
    """
    def __init__(self, movies: List[Movie]):
        self.movies = movies

    def predict(self, user: User, input_text: str) -> List[Movie]:
        
        # Тут должна быть логика предсказания самой модели. Пока что отдает первые 3 по порядку.
        model_prediction = self.movies[:3]
        return model_prediction
    