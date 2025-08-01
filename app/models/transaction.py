from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from constants import TransactionType, TransactionCost

if TYPE_CHECKING:
    from user import User
    from wallet import Wallet


class Transaction(SQLModel, table=True):
    """
    Класс для представления финансовой транзакции в системе.
    
    Attributes:
        id (int): Уникальный идентификатор транзакции
        user_id (int): ID юзера, по которому проходит транзакция
        wallet_id (int): ID Кошелька юзера
        amount (str): Положительное значение - пополнение, отрицательное - списание
        type (str): "deposit" - пополненик, "prediction" - списание, "admin_adjustment" - пополнение с правами админа
        description (str): Описание транзакции
        timestamp (datetime): Временная метка транзакции
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    wallet_id: int = Field(foreign_key="wallet.id", index=True)
    amount: TransactionCost = Field()
    type: TransactionType = Field()
    description: str = Field(min_length=1, max_length=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    wallet: "Wallet" = Relationship(back_populates="transactions")
    user: "User" = Relationship()
    

    def __post_init__(self) -> None:
        self._validate_type()
        self._validate_description()

    def _validate_type(self) -> None:
        """Проверяет тип события"""
        if not TransactionType.is_valid_type(self.type):
            raise ValueError("Неизвестный тип транзакции")
