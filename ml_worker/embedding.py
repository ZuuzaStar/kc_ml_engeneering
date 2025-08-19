from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer

    
class MLModel(ABC):
    """
    Абстрактный класс для самой ML модели
    """
    @abstractmethod
    def get_embedding(self, input_text: str) -> List[float]:
        pass


class EmbeddingGenerator(MLModel):
    """
    Получение рекомендаций для пользователя на основе ввода
    """
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer('sentence-transformers/' + model_name)
    
    def get_embedding(self, input_text: str) -> List[float]:
        """
        Получение эмбединга для запроса пользователя
        
        Args:
            input_text (str): Текстовый запрос пользователя
            
        Returns:
            List[float]: Список рекомендованных фильмов
        """
        embedding = self.model.encode(input_text)
        return embedding.tolist() if hasattr(embedding, 'tolist') else embedding
            
