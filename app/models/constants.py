from enum import Enum

class TransactionType(str, Enum):
    """Перечисление типов транзакций"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PREDICTION = "prediction"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class TransactionCost(float, Enum):
    """Перечисление стоимости транзакций в зависимости от тарифа"""
    BASIC = 10.0
    SUBSCRIPTION = 5.0
    ADMIN = 0.0
    BONUS = 20.0
    
    @classmethod
    def _missing_(cls, value):
        """
        Вызывается, когда значение не найдено в enum.
        Создает новый экземпляр с произвольным значением.
        """
        new_member = object.__new__(cls)
        new_member._name_ = f"USER_CUSTOM_VALUE"
        new_member._value_ = float(value)
        return new_member

class ModelTypes(str, Enum):
    """Перечисление возможных моделей, которые можно испрользовать"""
    BASIC = 'all-MiniLM-L6-v2'
    