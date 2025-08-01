from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
import re
from typing import TYPE_CHECKING
from constants import TransactionType, TransactionCost

if TYPE_CHECKING:
    from prediction import Prediction
    from transaction import Transaction
    from wallet import Wallet


class User(SQLModel, table=True):
    """
    Класс для представления пользователя.
    
    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Имейл адрес пользователя
        password_hash (str): Захешированный пароль пользователя
        is_admin (bool): По умолчанию пользователь - не админ
        wallet_id (int): ID кошелька юзера
        wallet (Waller): Кошелек пользователя с информацией о балансе и транзакциях
        predictions (List["Prediction"]): История рекомендаций
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, min_length=5, max_length=255)
    password_hash: str = Field(min_length=4, max_length=255)
    is_admin: bool = Field(default=False)
    wallet_id: Optional[int] = Field(default=None, foreign_key="wallet.id", unique=True)
    
    # Relationships
    wallet: Wallet = Relationship()
    predictions: List["Prediction"] = Relationship(back_populates="user")

    
    def __post_init__(self):
        self._validate_email()
    
    def _validate_email(self):
        """Проверяет что email похож на email"""
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.email):
            raise ValueError("Некорректный email")
        
class Admin(User):
    """
    Класс для представления пользователя с правами администратора.
    Наследуется от класса для представления пользователя.
    
    Attributes:
        is_admin (bool): Значение is_admin становится равно True
    """
    is_admin: bool = True

    # Пример привелигированной админской функциональности
    def adjust_balance(self, user: User, amount: float, description: str) -> "Transaction":
        transaction = Transaction(
            id=len(user.wallet.transactions) + 1,
            user_id=user.id,
            wallet_id=user.wallet.id,
            amount=TransactionCost(amount),
            type=TransactionType.ADMIN_ADJUSTMENT,
            description=description
        )
        user.wallet.make_transaction(transaction)
        return transaction
