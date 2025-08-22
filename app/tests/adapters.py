"""
Адаптеры для преобразования PostgreSQL типов в SQLite-совместимые
для unit-тестов
"""
from sqlalchemy import TypeDecorator, Text, String, Integer, Float, Boolean, DateTime, Column, ForeignKey
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.declarative import declarative_base
import json
from typing import List, Any, Union, Optional
import numpy as np
from datetime import datetime


class SQLiteArray(TypeDecorator):
    """Адаптер для эмуляции PostgreSQL ARRAY в SQLite"""
    impl = Text
    
    def process_bind_param(self, value: List[str], dialect):
        if value is None:
            return None
        if dialect.name == 'sqlite':
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'sqlite':
            return json.loads(value)
        return value


class SQLiteVector(TypeDecorator):
    """Адаптер для эмуляции PostgreSQL Vector в SQLite"""
    impl = Text
    
    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        if dialect.name == 'sqlite':
            if isinstance(value, np.ndarray):
                return json.dumps(value.tolist())
            elif isinstance(value, list):
                return json.dumps(value)
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'sqlite':
            return json.loads(value)
        return value


def get_sqlite_compatible_type(original_type):
    """Возвращает SQLite-совместимый тип для оригинального PostgreSQL типа"""
    type_mapping = {
        'ARRAY': SQLiteArray,
        'Vector': SQLiteVector,
    }
    
    # Простое определение типа по имени
    if hasattr(original_type, '__name__'):
        type_name = original_type.__name__
        if type_name in type_mapping:
            return type_mapping[type_name]
    
    return original_type


# Базовый класс для тестовых моделей
Base = declarative_base()


def create_sqlite_compatible_model(original_model_class):
    """
    Создает SQLite-совместимую версию модели на основе оригинальной
    
    Args:
        original_model_class: Оригинальный класс модели SQLModel
        
    Returns:
        Новый класс модели, совместимый с SQLite
    """
    
    # Получаем имя таблицы
    table_name = getattr(original_model_class, '__tablename__', None)
    if not table_name:
        raise ValueError(f"Модель {original_model_class.__name__} должна иметь __tablename__")
    
    # Создаем новый класс
    test_class_name = f"Test{original_model_class.__name__}"
    
    # Базовые поля
    fields = {
        '__tablename__': table_name,
        '__module__': original_model_class.__module__,
        'id': Column(Integer, primary_key=True, index=True),
    }
    
    # Анализируем поля оригинальной модели
    for field_name, field_info in original_model_class.__annotations__.items():
        if field_name == 'id':
            continue
            
        # Определяем тип поля
        field_type = _map_field_type(field_info, field_name)
        if field_type is not None:  # Исправлено: проверяем на None
            fields[field_name] = field_type
    
    # Создаем класс
    test_class = type(test_class_name, (Base,), fields)
    
    return test_class


def _map_field_type(field_info, field_name):
    """Маппинг типов полей для SQLite совместимости"""
    
    # Обрабатываем Union типы (например, Optional[str])
    if hasattr(field_info, '__origin__') and field_info.__origin__ is Union:
        # Берем первый не-None тип
        for arg in field_info.__args__:
            if arg != type(None):
                field_info = arg
                break
    
    # Базовые типы
    if field_info == str:
        return Column(String)
    elif field_info == int:
        return Column(Integer)
    elif field_info == float:
        return Column(Float)
    elif field_info == bool:
        return Column(Boolean)
    elif field_info == datetime:
        return Column(DateTime, default=datetime.utcnow)
    
    # Списки (эмулируем как JSON)
    elif hasattr(field_info, '__origin__') and field_info.__origin__ is list:
        return Column(Text)  # JSON строка
    
    # Специальные типы PostgreSQL
    elif hasattr(field_info, '__name__'):
        type_name = field_info.__name__
        if type_name in ['ARRAY', 'Vector']:
            return Column(Text)  # JSON строка
    
    # По умолчанию - Text
    return Column(Text)
