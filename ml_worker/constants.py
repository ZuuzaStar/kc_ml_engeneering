from enum import Enum
class ModelTypes(str, Enum):
    """Перечисление возможных моделей, которые можно испрользовать"""
    BASIC = 'all-MiniLM-L6-v2'
    