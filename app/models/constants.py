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
        # Создаем новый экземпляр с произвольным числовым значением
        obj = int.__new__(cls, value)
        obj._name_ = f"CUSTOM_USER_VALUE"
        obj._value_ = int(value)
        return obj
    
    # Магические методы сравнения
    def __lt__(self, other):
        """Меньше"""
        if isinstance(other, TransactionCost):
            return self.value < other.value
        return self.value < other
    
    def __le__(self, other):
        """Меньше или равно"""
        if isinstance(other, TransactionCost):
            return self.value <= other.value
        return self.value <= other
    
    def __gt__(self, other):
        """Больше"""
        if isinstance(other, TransactionCost):
            return self.value > other.value
        return self.value > other
    
    def __ge__(self, other):
        """Больше или равно"""
        if isinstance(other, TransactionCost):
            return self.value >= other.value
        return self.value >= other
    
    def __eq__(self, other):
        """Равно"""
        if isinstance(other, TransactionCost):
            return self.value == other.value
        return self.value == other
    
    def __ne__(self, other):
        """Не равно"""
        if isinstance(other, TransactionCost):
            return self.value != other.value
        return self.value != other

    # Магические методы сложения и вычитания
    def __add__(self, other):
        """Сложение"""
        if isinstance(other, TransactionCost):
            return self.value + other
        elif isinstance(other, (int, float)):
            return self.value + other
        return NotImplemented
    
    def __radd__(self, other):
        """Правое сложение (когда TransactionCost справа)"""
        return self.__add__(other)
    
    def __sub__(self, other):
        """Вычитание"""
        if isinstance(other, TransactionCost):
            return self.value - other
        elif isinstance(other, (int, float)):
            return self.value - other
        return NotImplemented
    
    def __rsub__(self, other):
        """Правое вычитание (когда TransactionCost справа)"""
        if isinstance(other, (int, float)):
            return other - self.value
        return NotImplemented

    # Унарные операции
    def __neg__(self):
        """Унарный минус (смена знака)"""
        return TransactionCost(-self.value)
    
    def __pos__(self):
        """Унарный плюс"""
        return TransactionCost(+self.value)
    
    def __abs__(self):
        """Абсолютное значение"""
        return TransactionCost(abs(self.value))