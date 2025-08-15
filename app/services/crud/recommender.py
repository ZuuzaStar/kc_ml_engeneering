from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod
from sqlmodel import Session, select
from app.models.prediction import Prediction
from app.services.crud.user import get_user_by_id
from database.database import engine
from models.movie import Movie
from models.constants import TransactionCost
from pgvector.sqlalchemy import Vector
from models.user import User

if TYPE_CHECKING:
    from models.movie import Movie

    
class MLModel(ABC):
    """
    Абстрактный класс для самой ML модели
    """
    @abstractmethod
    def predict(self, user: User, input_text: str, top: int = 10) -> List['Movie']:
        pass


class MovieRecommender(MLModel):
    """
    Получение рекомендаций для пользователя на основе ввода
    """
    def predict(self, model, user: User, input_text: str, top: int = 10) -> List['Movie']:
        """
        Реализация абстрактного метода predict
        
        Args:
            input_text (str): Текстовый запрос пользователя
            top (int): Количество рекомендаций для возврата
            
        Returns:
            List[Movie]: Список рекомендованных фильмов
        """
        with Session(engine) as session:
            if not session.get(User, user.id):
                raise ValueError("Пользователя с таким id не существует")

            if user.is_admin:
                cost = TransactionCost.ADMIN.value
            else:
                cost = TransactionCost.BASIC.value

            # Генерация эмбеддинга для запроса
            embedding = model.encode(input_text).tolist()
            
            # Поиск похожих фильмов
            movies = session.scalars(
                select(Movie)
                .order_by(Movie.embedding.cast(Vector).op("<=>")(embedding))
                .limit(top)
            ).all()

            prediction = Prediction(
                user_id=user.id,
                input_text=input_text,
                cost=cost,
                user=user,
                movies=movies
            )
            
            session.add(prediction)
            user.predictions.append(prediction)
            session.refresh(user)
            session.commit()

            return movies
