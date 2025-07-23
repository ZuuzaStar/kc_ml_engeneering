from dataclasses import dataclass, field
from typing import List, Dict, Optional, Protocol
import re
from datetime import datetime
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import os
import bcrypt

load_dotenv() # Загружаем глобальные переменные


@dataclass
class PredictionHistory:
    """
    Класс для представления истории предсказаний.
    
    Attributes:
        predictions (List["Prediction"]): Актуальный список предсказаний
    """
    predictions: List["Prediction"] = field(default_factory=list)

    def add(self, prediction: "Prediction"):
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

@dataclass
class Transaction:
    """
    Класс для представления финансовой транзакции в системе.
    
    Attributes:
        id (int): Уникальный идентификатор транзакции
        user (User): Пользователь, для которого проходит транзакция
        amount (str): Положительное значение - пополнение, отрицательное - списание
        type (str): "deposit" - пополненик, "prediction" - списание, "admin_adjustment" - пополнение с правами админа
        description (str): Описание транзакции
        timestamp (datetime): Временная метка транзакции
    """
    id: int
    user: User
    amount: float
    type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self._validate_type()
        self._validate_description()

    def _validate_type(self) -> None:
        """Проверяет тип события"""
        allowed_types = os.getenv("ACTUAL_TRANSACTION_TYPES", "").split(',')
        if self.type in allowed_types:
            raise ValueError("Неизвестный тип транзакции")

    def _validate_description(self) -> None:
        """Проверяет длину описания события"""
        if len(self.description) == 0:
            raise ValueError("Описание не может быть пустым")

@dataclass
class Movie:
    """
    Класс для представления фильма, который модель может использовать для рекомендации.
    
    Attributes:
        id (int): Уникальный идентификатор фильма
        title (str): Название фильма
        description (str): Описание фильма
        cover_image_url (str): URL изображения обложки фильма
    """
    id: int
    title: str
    description: str
    cover_image_url: str

    def __post_init__(self):
        self._validate_title()
        self._validate_description()

    def _validate_title(self):
        if len(self.title) < 1:
            raise ValueError("Название фильма должно быть не короче одного символа")

    def _validate_description(self):
        if len(self.description) < 10:
            raise ValueError("Описание фильма не должно быть короче 10 символов")
        
    def change_title(self, new_title: str):
        """Возможность исправлять ошибки в названии"""
        self.title = new_title
    
    def change_description(self, new_description: str):
        """Возможность исправлять ошибки в описании"""
        self.description = new_description

@dataclass
class Prediction:
    """
    Класс для представления списка рекомендаций фильмов.
    
    Attributes:
        id (int): Уникальный идентификатор рекомендации
        user (User): Пользователь, для которого предлагается рекомендация
        input_text (str): Промт пользователя
        results (List[Movie]): Список рекомендованных фильмов
        cost (float): Стоимость генерации рекомендаций
        timestamp (datetime): Время запроса от пользователя
        is_success (bool): Успешен ли запрос
        error_message (str): Текст ошибки, если предсказание не удалось. По умолчанию "".
    """
    id: int
    user: User
    input_text: str
    results: List[Movie] = field(default_factory=list)
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    is_success: bool = True
    error_code: int = 0

    def __post_init__(self) -> None:
        self._validate_input_text()

    def _validate_input_text(self) -> None:
        """Проверяет, что запрос удовлетворяет требованиям"""
        if len(self.input_text) < 10:
            raise ValueError("Запрос должен быть длинне 10 символов")

class MLModel(ABC):
    """
    Абстрактный класс для самой ML модели
    """
    @abstractmethod
    def predict(self, input_text: str) -> List[Movie]:
        pass

class MovieRecommender(MLModel):
    """
    Класс, который наследует модель, список фильмов в базе и имеет метод predict
    Attributes:
        movies (List[Movie]): Список объектов фильмов из которых модель будет рекомендовать
    """
    def __init__(self, movies: List[Movie]):
        self.movies = movies

    def predict(self, user: User, input_text: str) -> List[Movie]:
        # Тут должна быть логика предсказания самой модели. Пока что отдает первые 3 по порядку.
        model_prediction = self.movies[:3]
        prediction = Prediction(
            id=len(user.prediction_history.predictions) + 1,
            user=user,
            input_text=input_text,
            results=model_prediction,
            cost=float(os.getenv("PREDICTION_COST"))
        )
        user.prediction_history.add(prediction)
        return model_prediction
    

class MovieService:
    """
    Класс для представления функуиональности самого сервиса.
    
    Attributes:
        users (Dict[int, User]): Словарь из всех пользователей на площадке [id, User]
        movies (Dict[int, User]): Словарь из всех фильмов на площадке [id, User]
        recomender (Optional[MovieRecommender]): Опционально, добавляется класс модели с возможностью предсказания
    """
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.movies: Dict[int, Movie] = {}
        self.recomender: Optional[MovieRecommender] = None

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def register_user(self, email: str, password: str) -> User:
        """Регистрация нового пользователя"""
        user_id = max(self.users.keys(), default=0) + 1
        password_hash = self._hash_password(password)
        
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash
        )
        
        self.users[user_id] = user
        
        # Добавляем стартовый бонус
        bonus = Transaction(
            id=1,
            user=user,
            amount=20.0,
            type="deposit",
            description="Приветственный бонус при регистрации"
        )
        user.wallet.make_transaction(bonus)
        user.transaction_history.add(bonus)

        return user

    def add_funds(self, user_id: int, amount: float) -> Transaction:
        """Пополнение баланса пользователем"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        transaction = Transaction(
            id=len(user.wallet.transactions) + 1,
            user=user,
            amount=amount,
            type="deposit",
            description="Пополнение баланса"
        )
        user.wallet.make_transaction(transaction)
        user.transaction_history.add(transaction)
        return transaction

    def admin_adjust_balance(self, user_id: int, amount: float) -> Transaction:
        """Административное изменение баланса"""
        user = self.users.get(user_id)
        if not user.is_admin:
            raise PermissionError("Требуются права администратора")
        if not user:
            raise ValueError("Пользователь не найден")
        
        return user.adjust_balance(user, amount, f"Корректировка администратором #{user.id}")

    def get_user_predictions_history(self, user_id: int) -> List[Prediction]:
        """Получение истории запросов пользователя"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        elif user.is_admin or user.id == user_id:
            return user.prediction_history.predictions
        else:
            raise PermissionError("Требуются права администратора")
        
    def get_user_transactions_history(self, user_id: int) -> List[Prediction]:
        """Получение истории запросов пользователя"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        elif user.is_admin or user.id == user_id:
            return user.transaction_history.transactions
        else:
            raise PermissionError("Требуются права администратора")

    def recommend_movies(self, user_id: int, input_text: str) -> Prediction:
        """Получение рекомендаций с валидацией и списанием средств"""
        self.ml_model = self.recomender(list(self.movies.values()))
        if not self.ml_model:
            raise ValueError("ML модель не инициализирована")
            
        # Проверка наличия юзера
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        else:
            prediction = Prediction(
                id=len(user.prediction_history.predictions) + 1,
                user=user,
                input_text=input_text,
                results=list(),
                cost=float(os.getenv("PREDICTION_COST")),
                is_success=False,
                error_code=1
            )

        # Проверка баланса и оздание записи о запросе
        if user.wallet.balance < float(os.getenv("PREDICTION_COST")) and not user.is_admin:
            user.prediction_history.add(prediction)
            raise ValueError("Недостаточно средств на балансе")
         
        try:
            # Использование ML модели
            prediction.results = self.ml_model.predict(user, input_text)
        except:
            user.prediction_history.add(prediction)
            prediction.error_code=2
            raise ValueError("Не удалось получить предсказания")
        
        try:
            # Списание средств (если не админ)
            if not user.is_admin:
                transaction = Transaction(
                    id=len(user.wallet.transactions) + 1,
                    user=user,
                    amount=-float(os.getenv("PREDICTION_COST")),
                    type="prediction",
                    description=f"Запрос рекомендаций #{prediction.id}"
                )
                user.wallet.make_transaction(transaction)
                user.transaction_history.add(transaction)
        except:
            user.prediction_history.add(prediction)
            raise ValueError("Не удалось совершить транзакцию")
        
        prediction.is_success=True
        prediction.error_code=0
        user.prediction_history.add(prediction)
        return prediction
