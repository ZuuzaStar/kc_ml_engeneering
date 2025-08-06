from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.transaction import Transaction
    from models.user import User


class Wallet(SQLModel, table=True):
    """
    Класс для представления кошелька пользователя.
    
    Attributes:
        id (int): ID кошелька
        user_id (int): ID владельца кошелька (юзера)
        balance (float): Текущий баланс средств
        created_at (datetime): Дата и время создания кошелька
        transactions (List["Transaction"]): История транзакций        
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", unique=True)
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships    
    transactions: Mapped[List["Transaction"]] = Relationship(back_populates="wallet")
    user: Mapped[Optional['User']] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Wallet.user_id"}
    )
