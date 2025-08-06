from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
import re
from typing import TYPE_CHECKING
from pydantic import field_validator
import bcrypt
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from models.prediction import Prediction
    from models.wallet import Wallet


class User(SQLModel, table=True):
    """
    Класс для представления пользователя.
    
    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Имейл адрес пользователя
        password_hash (str): Захешированный пароль пользователя
        is_admin (bool): По умолчанию пользователь - не админ
        wallet_id (int): ID кошелька юзера
        wallet (Wallet): Кошелек пользователя с информацией о балансе и транзакциях
        predictions (List["Prediction"]): История рекомендаций
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, min_length=5, max_length=255)
    password_hash: str = Field(min_length=4, max_length=255)
    is_admin: bool = Field(default=False)
    wallet_id: Optional[int] = Field(default=None, foreign_key="wallet.id", unique=True)
    
    # Relationships
    wallet: Mapped[Optional["Wallet"]] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "User.wallet_id"}
    )
    predictions: Mapped[List["Prediction"]] = Relationship(back_populates="user")

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> bool:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ValueError("Неверный формат email")
        return True

    def _validate_password(self, password: str) -> bool:
        """
        Проверяет что переданный пароль соответствует актуальному паролю юзера.
        
        Args:
            user: объект текущего пользователя
            password: строка для сравнения с паролем
        
        Returns:
            bool: возвращает True, если соответствует, иначе - ошибка
        """
        if not bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8")):
            raise ValueError("Некорректный пароль")
        return True
