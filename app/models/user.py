from __future__ import annotations
from sqlmodel import Field, Relationship
from typing import List, Optional
import re
from typing import TYPE_CHECKING
from pydantic import field_validator
import bcrypt
from models.base_model import BaseModel
from sqlalchemy.orm import Mapped, relationship


if TYPE_CHECKING:
    from models.prediction import Prediction
    from models.wallet import Wallet


class User(BaseModel, table=True):
    """
    Класс для представления пользователя.
    
    Attributes:
        email (str): Имейл адрес пользователя
        password_hash (str): Захешированный пароль пользователя
        is_admin (bool): По умолчанию пользователь - не админ
        wallet_id (Optional[int]): ID кошелька юзера
    
    Relationships:
        wallet (Mapped[Optional["Wallet"]]): Кошелек пользователя с информацией о балансе и транзакциях
        predictions (Mapped[List["Prediction"]]): История рекомендаций
    """
    email: str = Field(unique=True, index=True, min_length=5, max_length=255)
    password_hash: str = Field(min_length=4, max_length=255)
    is_admin: bool = Field(default=False)
    wallet: Mapped[Optional["Wallet"]] = Relationship(sa_relationship=relationship(back_populates="user"))
    predictions: Mapped[List["Prediction"]]= Relationship(sa_relationship=relationship(back_populates="user"))

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ValueError("Неверный формат email")
        return email
    
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
