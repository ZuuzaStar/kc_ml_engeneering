from dataclasses import dataclass, field
from typing import List
import re
import bcrypt
from prediction import Prediction
from transaction import Transaction

@dataclass
class PredictionHistory:
    """
    Класс для представления истории предсказаний.
    
    Attributes:
        predictions (List['Prediction']): Актуальный список предсказаний
    """
    predictions: List['Prediction'] = field(default_factory=list)

    def add(self, prediction: 'Prediction'):
        self.predictions.append(prediction)


@dataclass
class TransactionHistory:
    """
    Класс для представления истории транзакций.
    
    Attributes:
        transactions (List['Transaction']): Актуальный список транзакций
    """
    transactions: List['Transaction'] = field(default_factory=list)

    def add(self, transaction: 'Transaction'):
        self.transactions.append(transaction)

@dataclass
class Wallet:
    """
    Класс для представления кошелька пользователя.
    
    Attributes:
        balance (float): Текущий баланс средств
        transactions (List['Transaction']): История транзакций
    """
    balance: float = 0.0
    transactions: List['Transaction'] = field(default_factory=list)

    def make_transaction(self, transaction: 'Transaction'):
        self.transactions.append(transaction)
        self.balance += transaction.amount

@dataclass
class User:
    """
    Класс для представления пользователя.
    
    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Имейл адрес пользователя
        password_hash (str): Захешированный пароль пользователя
        is_admin (bool): По умолчанию пользователь - не админ
        wallet (Waller): Кошелек пользователя с информацией о балансе и транзакциях
        prediction_history (PredictionHistory): История рекомендаций
        transaction_history (TransactionHistory): История финансовых транзакций
    """
    id: int
    email: str
    password_hash: str
    is_admin: bool = False
    wallet: Wallet = field(default_factory=Wallet)
    prediction_history: PredictionHistory = field(default_factory=PredictionHistory)
    transaction_history: TransactionHistory = field(default_factory=TransactionHistory)
    
    def __post_init__(self):
        self._validate_email()
    
    def _validate_email(self):
        """Проверяет что email похож на email"""
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.email):
            raise ValueError("Некорректный email")
    
    def validate_password(self, password: str):
        """Проверяет что переданный пароль - верный"""
        if not bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8")):
            raise ValueError("Некорректный пароль")
        
@dataclass
class Admin(User):
    """
    Класс для представления пользователя с правами администратора.
    Наследуется от класса для представления пользователя.
    
    Attributes:
        is_admin (bool): Значение is_admin становится равно True
    """
    is_admin: bool = True

    # Пример привелигированной админской функциональности
    def adjust_balance(self, user: User, amount: float, description: str) -> 'Transaction':
        transaction = Transaction(
            id=len(user.wallet.transactions) + 1,
            user=user,
            amount=amount,
            type="admin_adjustment",
            description=description
        )
        user.wallet.make_transaction(transaction)
        user.transaction_history.add(transaction)
        return transaction