from typing import List
from abc import ABC, abstractmethod
import os
from movie import Movie
from user import User
from prediction import Prediction


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
        prediction = Prediction(
            id=len(user.prediction_history.predictions) + 1,
            user=user,
            input_text=input_text,
            results=model_prediction,
            cost=float(os.getenv("PREDICTION_COST", 10))
        )
        user.prediction_history.add(prediction)
        return model_prediction