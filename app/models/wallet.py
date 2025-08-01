from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transaction import Transaction


class Wallet(SQLModel, table=True):
    """
    Класс для представления кошелька пользователя.
    
    Attributes:
        id (int): ID кошелька
        balance (float): Текущий баланс средств
        transactions (List["Transaction"]): История транзакций
        created_at (datetime): Дата и время создания кошелька
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transactions: List["Transaction"] = Relationship(back_populates="wallet")