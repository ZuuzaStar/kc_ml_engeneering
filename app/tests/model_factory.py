"""
Фабрика для создания тестовых версий моделей с использованием адаптеров
"""
import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters import create_sqlite_compatible_model, Base
from typing import Dict, Type


class TestModelFactory:
    """Фабрика для создания тестовых версий моделей"""
    
    @staticmethod
    def create_all_test_models() -> Dict[str, Type]:
        """
        Создает все необходимые тестовые модели на основе оригинальных
        
        Returns:
            Словарь с тестовыми моделями
        """
        
        # Импортируем оригинальные модели
        try:
            from models.user import User
            from models.wallet import Wallet
            from models.transaction import Transaction
            from models.movie import Movie
            from models.prediction import Prediction
            
            # Создаем тестовые версии
            test_models = {
                'TestUser': create_sqlite_compatible_model(User),
                'TestWallet': create_sqlite_compatible_model(Wallet),
                'TestTransaction': create_sqlite_compatible_model(Transaction),
                'TestMovie': create_sqlite_compatible_model(Movie),
                'TestPrediction': create_sqlite_compatible_model(Prediction),
            }
            
            return test_models
            
        except ImportError as e:
            print(f"Ошибка импорта моделей: {e}")
            return {}
    
    @staticmethod
    def get_test_model(model_name: str) -> Type:
        """
        Получает тестовую модель по имени
        
        Args:
            model_name: Имя модели (например, 'User', 'Movie')
            
        Returns:
            Тестовый класс модели
        """
        test_models = TestModelFactory.create_all_test_models()
        test_model_name = f"Test{model_name}"
        
        if test_model_name not in test_models:
            raise ValueError(f"Тестовая модель {test_model_name} не найдена")
        
        return test_models[test_model_name]


# Глобальные тестовые модели
TEST_MODELS = TestModelFactory.create_all_test_models()

# Удобные алиасы
TestUser = TEST_MODELS.get('TestUser')
TestWallet = TEST_MODELS.get('TestWallet')
TestTransaction = TEST_MODELS.get('TestTransaction')
TestMovie = TEST_MODELS.get('TestMovie')
TestPrediction = TEST_MODELS.get('TestPrediction')
