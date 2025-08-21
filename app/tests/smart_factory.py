"""
Умная фабрика для создания тестовых моделей с наследованием от оригинальных
"""
import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel, Field
from typing import Type, Dict, Any, List, Optional
from datetime import datetime
import json


class SmartTestModelFactory:
    """Умная фабрика для создания тестовых моделей"""
    
    @staticmethod
    def create_test_models() -> Dict[str, Type[SQLModel]]:
        """
        Создает тестовые модели, наследуя от оригинальных
        
        Returns:
            Словарь с тестовыми моделями
        """
        
        try:
            # Импортируем оригинальные модели
            from models.user import User
            from models.wallet import Wallet
            from models.transaction import Transaction
            from models.movie import Movie
            from models.prediction import Prediction
            
            # Создаем тестовые версии
            test_models = {
                'TestUser': SmartTestModelFactory._create_test_user(User),
                'TestWallet': SmartTestModelFactory._create_test_wallet(Wallet),
                'TestTransaction': SmartTestModelFactory._create_test_transaction(Transaction),
                'TestMovie': SmartTestModelFactory._create_test_movie(Movie),
                'TestPrediction': SmartTestModelFactory._create_test_prediction(Prediction),
            }
            
            return test_models
            
        except ImportError as e:
            print(f"Ошибка импорта моделей: {e}")
            return {}
    
    @staticmethod
    def _create_test_user(original_user: Type[SQLModel]) -> Type[SQLModel]:
        """Создает тестовую версию User"""
        
        class TestUser(original_user):
            # Переопределяем проблемные поля
            pass
        
        return TestUser
    
    @staticmethod
    def _create_test_wallet(original_wallet: Type[SQLModel]) -> Type[SQLModel]:
        """Создает тестовую версию Wallet"""
        
        class TestWallet(original_wallet):
            # Переопределяем проблемные поля
            pass
        
        return TestWallet
    
    @staticmethod
    def _create_test_transaction(original_transaction: Type[SQLModel]) -> Type[SQLModel]:
        """Создает тестовую версию Transaction"""
        
        class TestTransaction(original_transaction):
            # Переопределяем проблемные поля
            pass
        
        return TestTransaction
    
    @staticmethod
    def _create_test_movie(original_movie: Type[SQLModel]) -> Type[SQLModel]:
        """Создает тестовую версию Movie с SQLite-совместимыми типами"""
        
        class TestMovie(original_movie):
            # Переопределяем проблемные поля для SQLite
            genres: str = Field()  # Вместо ARRAY(String)
            embedding: str = Field()  # Вместо Vector(384)
            
            def __init__(self, **data):
                # Преобразуем данные при создании
                if 'genres' in data and isinstance(data['genres'], list):
                    data['genres'] = json.dumps(data['genres'])
                if 'embedding' in data and isinstance(data['embedding'], (list, tuple)):
                    data['embedding'] = json.dumps(data['embedding'])
                super().__init__(**data)
            
            @property
            def genres_list(self) -> List[str]:
                """Возвращает жанры как список"""
                try:
                    return json.loads(self.genres)
                except (json.JSONDecodeError, TypeError):
                    return []
            
            @property
            def embedding_vector(self) -> List[float]:
                """Возвращает эмбединг как список"""
                try:
                    return json.loads(self.embedding)
                except (json.JSONDecodeError, TypeError):
                    return []
        
        return TestMovie
    
    @staticmethod
    def _create_test_prediction(original_prediction: Type[SQLModel]) -> Type[SQLModel]:
        """Создает тестовую версию Prediction с SQLite-совместимыми типами"""
        
        class TestPrediction(original_prediction):
            # Переопределяем проблемные поля для SQLite
            embedding: str = Field()  # Вместо Vector(384)
            
            def __init__(self, **data):
                # Преобразуем данные при создании
                if 'embedding' in data and isinstance(data['embedding'], (list, tuple)):
                    data['embedding'] = json.dumps(data['embedding'])
                super().__init__(**data)
            
            @property
            def embedding_vector(self) -> List[float]:
                """Возвращает эмбединг как список"""
                try:
                    return json.loads(self.embedding)
                except (json.JSONDecodeError, TypeError):
                    return []
        
        return TestPrediction


# Глобальные тестовые модели
TEST_MODELS = SmartTestModelFactory.create_test_models()

# Удобные алиасы
TestUser = TEST_MODELS.get('TestUser')
TestWallet = TEST_MODELS.get('TestWallet')
TestTransaction = TEST_MODELS.get('TestTransaction')
TestMovie = TEST_MODELS.get('TestMovie')
TestPrediction = TEST_MODELS.get('TestPrediction')
