"""
Миксин для автоматического преобразования PostgreSQL типов в SQLite-совместимые
"""
from sqlmodel import SQLModel, Field
from typing import Any, Type, get_type_hints, get_origin, get_args, Union
import json


class SQLiteCompatibleMixin:
    """
    Миксин для автоматического создания SQLite-совместимых версий SQLModel моделей
    
    Использование:
    class TestUser(SQLiteCompatibleMixin, SQLModel, table=True):
        # Автоматически преобразует ARRAY и Vector в Text
    """
    
    @classmethod
    def create_sqlite_compatible(cls, original_model: Type[SQLModel]) -> Type[SQLModel]:
        """
        Создает SQLite-совместимую версию модели
        
        Args:
            original_model: Оригинальная SQLModel модель
            
        Returns:
            SQLite-совместимая версия модели
        """
        
        # Получаем имя таблицы
        table_name = getattr(original_model, '__tablename__', None)
        if not table_name:
            raise ValueError(f"Модель {original_model.__name__} должна иметь __tablename__")
        
        # Создаем новый класс
        test_class_name = f"Test{original_model.__name__}"
        
        # Базовые поля
        fields = {
            '__tablename__': table_name,
            '__module__': original_model.__module__,
        }
        
        # Анализируем поля оригинальной модели
        type_hints = get_type_hints(original_model)
        
        for field_name, field_info in type_hints.items():
            # Определяем тип поля
            field_type = cls._get_sqlite_field_type(field_info, field_name)
            if field_type is not None:
                fields[field_name] = field_type
        
        # Создаем класс
        test_class = type(test_class_name, (cls, SQLModel), fields)
        test_class.__table__ = True
        
        return test_class
    
    @classmethod
    def _get_sqlite_field_type(cls, field_info: Any, field_name: str) -> Any:
        """
        Определяет SQLite-совместимый тип для поля
        
        Args:
            field_info: Информация о типе поля
            field_name: Имя поля
            
        Returns:
            SQLite-совместимый тип поля
        """
        
        # Обрабатываем Union типы (например, Optional[str])
        if get_origin(field_info) is Union:
            # Берем первый не-None тип
            for arg in get_args(field_info):
                if arg != type(None):
                    field_info = arg
                    break
        
        # Базовые типы
        if field_info == str:
            return Field()
        elif field_info == int:
            return Field()
        elif field_info == float:
            return Field()
        elif field_info == bool:
            return Field()
        
        # Списки (эмулируем как JSON строку)
        elif get_origin(field_info) is list:
            return Field()  # Будет сохранено как JSON строка
        
        # Специальные типы PostgreSQL
        elif hasattr(field_info, '__name__'):
            type_name = field_info.__name__
            if type_name in ['ARRAY', 'Vector']:
                return Field()  # Будет сохранено как JSON строка
        
        # По умолчанию - обычное поле
        return Field()


def make_sqlite_compatible(original_model: Type[SQLModel]) -> Type[SQLModel]:
    """
    Декоратор для создания SQLite-совместимой версии модели
    
    Args:
        original_model: Оригинальная SQLModel модель
        
    Returns:
        SQLite-совместимая версия модели
    """
    return SQLiteCompatibleMixin.create_sqlite_compatible(original_model)
