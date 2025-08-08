from __future__ import annotations
from sqlmodel import Field, Relationship
from typing import List, Optional
from typing import TYPE_CHECKING
from models.base_model import BaseModel
from sqlalchemy.orm import Mapped, relationship

if TYPE_CHECKING:
    from models.transaction import Transaction
    from models.user import User


class Wallet(BaseModel, table=True):
    """
    Класс для представления кошелька пользователя.

    Attributes:
        balance (float): Текущий баланс средств

    Relationships:
        transactions (Mapped[List["Transaction"]]): История транзакций
        user (Mapped[Optional["User"]]): Связь с владельцем кошелька
    """
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", unique=True)
    balance: float = Field(default=0.0)
    transactions: Mapped[List["Transaction"]] = Relationship(
        sa_relationship=relationship(back_populates="wallet")
    )
    user: Mapped[Optional["User"]] = Relationship(
        sa_relationship=relationship(back_populates="wallet")
    )
