from dataclasses import dataclass, field
from datetime import datetime
import os
from user import User

@dataclass
class Transaction:
    """
    Класс для представления финансовой транзакции в системе.
    
    Attributes:
        id (int): Уникальный идентификатор транзакции
        user (User): Пользователь, для которого проходит транзакция
        amount (str): Положительное значение - пополнение, отрицательное - списание
        type (str): "deposit" - пополненик, "prediction" - списание, "admin_adjustment" - пополнение с правами админа
        description (str): Описание транзакции
        timestamp (datetime): Временная метка транзакции
    """
    id: int
    user: User
    amount: float
    type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self._validate_type()
        self._validate_description()

    def _validate_type(self) -> None:
        """Проверяет тип события"""
        allowed_types = os.getenv("ACTUAL_TRANSACTION_TYPES", "").split(',')
        if self.type in allowed_types:
            raise ValueError("Неизвестный тип транзакции")

    def _validate_description(self) -> None:
        """Проверяет длину описания события"""
        if len(self.description) == 0:
            raise ValueError("Описание не может быть пустым")