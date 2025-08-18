from __future__ import annotations
from sqlmodel import Field, Relationship
from typing import Optional, TYPE_CHECKING
from models.constants import TransactionType
from models.base_model import BaseModel
from sqlalchemy.orm import Mapped, relationship

if TYPE_CHECKING:
    from models.user import User
    from models.wallet import Wallet


class Transaction(BaseModel, table=True):
    """
    Класс для представления финансовой транзакции в системе.
    
    Attributes:
        user_id (int): ID юзера, по которому проходит транзакция
        wallet_id (int): ID Кошелька юзера
        amount (float): Положительное значение - пополнение, отрицательное - списание
        type (TransactionType): Тип транзакции
        description (Optional[str]): Описание транзакции

    Relationships:
        wallet ("Wallet"): Связь транзакции с кошельком
        user ("User"): Связь транзакции с юзером
    """
    user_id: int = Field(foreign_key="user.id", index=True)
    wallet_id: int = Field(foreign_key="wallet.id", index=True)
    amount: float = Field(default=0.0)
    type: TransactionType = Field()
    
    # Relationships
    wallet: Mapped["Wallet"] = Relationship(sa_relationship=relationship(back_populates="transactions"))
    user: Mapped["User"] = Relationship(sa_relationship=relationship())
