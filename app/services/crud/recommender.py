from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod
from sqlmodel import Session, select
from database.database import engine
from models.movie import Movie
from models.constants import ModelTypes
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from models.movie import Movie

    
class MLModel(ABC):
    """
    Абстрактный класс для самой ML модели
    """
    @abstractmethod
    def predict(self, input_text: str) -> List['Movie']:
        pass


class MovieRecommender(MLModel):
    """
    Получение рекомендаций для пользователя на основе ввода
    
    Attributes:
        model: SentenceTransformer модель для генерации эмбеддингов
    """
    
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/' + ModelTypes.BASIC.value)

    def predict(self, input_text: str, top: int = 10) -> List['Movie']:
        """
        Реализация абстрактного метода predict
        
        Args:
            input_text (str): Текстовый запрос пользователя
            top (int): Количество рекомендаций для возврата
            
        Returns:
            List[Movie]: Список рекомендованных фильмов
        """
        with Session(engine) as session:
            # Генерация эмбеддинга для запроса
            embedding = self.model.encode(input_text).tolist()
            
            # Поиск похожих фильмов
            movies = session.scalars(
                select(Movie)
                .order_by(Movie.embedding.cast(Vector).op("<=>")(embedding))
                .limit(top)
            ).all()
            
            return movies  # Возвращаем объекты Movie
