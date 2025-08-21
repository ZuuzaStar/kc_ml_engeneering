"""
Простая фабрика для создания тестовых моделей
"""
import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel, Field
from typing import Type, Dict, Any, List, Optional
from datetime import datetime
import json


class SimpleTestModelFactory:
    """Простая фабрика для создания тестовых моделей"""
    
    @staticmethod
    def create_test_models() -> Dict[str, Type[SQLModel]]:
        """
        Создает тестовые модели, копируя структуру оригинальных
        
        Returns:
            Словарь с тестовыми моделями
        """
        
        # Создаем тестовые версии напрямую
        test_models = {
            'TestUser': SimpleTestModelFactory._create_test_user(),
            'TestWallet': SimpleTestModelFactory._create_test_wallet(),
            'TestTransaction': SimpleTestModelFactory._create_test_transaction(),
            'TestMovie': SimpleTestModelFactory._create_test_movie(),
            'TestPrediction': SimpleTestModelFactory._create_test_prediction(),
        }
        
        return test_models
    
    @staticmethod
    def _create_test_user() -> Type[SQLModel]:
        """Создает тестовую версию User"""
        
        class TestUser(SQLModel, table=True):
            __tablename__ = "user"
            
            id: Optional[int] = Field(default=None, primary_key=True)
            email: str = Field(unique=True, index=True)
            password_hash: str
            is_admin: bool = Field(default=False)
            timestamp: datetime = Field(default_factory=datetime.utcnow)
        
        return TestUser
    
    @staticmethod
    def _create_test_wallet() -> Type[SQLModel]:
        """Создает тестовую версию Wallet"""
        
        class TestWallet(SQLModel, table=True):
            __tablename__ = "wallet"
            
            id: Optional[int] = Field(default=None, primary_key=True)
            user_id: int = Field(foreign_key="user.id", unique=True)
            balance: float = Field(default=0.0)
            timestamp: datetime = Field(default_factory=datetime.utcnow)
        
        return TestWallet
    
    @staticmethod
    def _create_test_transaction() -> Type[SQLModel]:
        """Создает тестовую версию Transaction"""
        
        class TestTransaction(SQLModel, table=True):
            __tablename__ = "transaction"
            
            id: Optional[int] = Field(default=None, primary_key=True)
            user_id: int = Field(foreign_key="user.id", index=True)
            wallet_id: int = Field(foreign_key="wallet.id", index=True)
            amount: float = Field(default=0.0)
            type: str
            description: Optional[str] = None
            timestamp: datetime = Field(default_factory=datetime.utcnow)
        
        return TestTransaction
    
    @staticmethod
    def _create_test_movie() -> Type[SQLModel]:
        """Создает тестовую версию Movie с SQLite-совместимыми типами"""
        
        class TestMovie(SQLModel, table=True):
            __tablename__ = "movie"
            
            id: Optional[int] = Field(default=None, primary_key=True)
            title: str
            description: str = Field(unique=True)
            year: int
            genres: str = Field()  # JSON строка для эмуляции ARRAY
            embedding: str = Field()  # JSON строка для эмуляции Vector
            timestamp: datetime = Field(default_factory=datetime.utcnow)
            
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
    def _create_test_prediction() -> Type[SQLModel]:
        """Создает тестовую версию Prediction с SQLite-совместимыми типами"""
        
        class TestPrediction(SQLModel, table=True):
            __tablename__ = "prediction"
            
            id: Optional[int] = Field(default=None, primary_key=True)
            user_id: int = Field(foreign_key="user.id", index=True)
            input_text: str
            embedding: str = Field()  # JSON строка для эмуляции Vector
            cost: float = Field(default=0.0)
            timestamp: datetime = Field(default_factory=datetime.utcnow)
            
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
TEST_MODELS = SimpleTestModelFactory.create_test_models()

# Удобные алиасы
TestUser = TEST_MODELS.get('TestUser')
TestWallet = TEST_MODELS.get('TestWallet')
TestTransaction = TEST_MODELS.get('TestTransaction')
TestMovie = TEST_MODELS.get('TestMovie')
TestPrediction = TEST_MODELS.get('TestPrediction')
