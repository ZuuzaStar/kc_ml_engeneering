from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import TYPE_CHECKING
from models.base_model import BaseModel

if TYPE_CHECKING:
    from models.transaction import Transaction
    from models.user import User


class Wallet(BaseModel, table=True):
    """
    Класс для представления кошелька пользователя.
    
    Attributes:
        user_id (Optional[int]): ID владельца кошелька (юзера)
        balance (float): Текущий баланс средств
    
    Relationships:
        transactions (Mapped[List["Transaction"]]): История транзакций   
        user (Mapped[Optional['User']]): Связь с владельцем кошелька     
    """
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", unique=True)
    balance: float = Field(default=0.0)
    transactions: Mapped[List["Transaction"]] = Relationship(back_populates="wallet")
    user: Optional['User'] = Relationship(back_populates="wallet")