from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod
import os
from database.database import engine
from sqlmodel import Session

if TYPE_CHECKING:
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
        cost = float(os.getenv("PREDICTION_COST", "10.0"))
        if user.wallet.balance < cost:
            raise ValueError("Недостаточно средств для получения рекомендаций")
        user.wallet.balance -= cost

        # Тут должна быть логика предсказания самой модели. Пока что отдает первые 3 по порядку.
        model_prediction = self.movies[:3]

        prediction = Prediction(
            id=len(user.prediction_history.predictions) + 1,
            user_id=user.id,
            input_text=input_text,
            cost=float(os.getenv("PREDICTION_COST", 10)),
            results=model_prediction,
        )
        # user.predictions.append(prediction)
        # Сохраняем в базу данных
        with Session(engine) as session:
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            
            # Создаем связи с фильмами через PredictionMovieLink
            from models.prediction import PredictionMovieLink
            for movie in model_prediction:
                link = PredictionMovieLink(
                    prediction_id=prediction.id,
                    movie_id=movie.id
                )
                session.add(link)
            session.commit()
        
        return model_prediction
    