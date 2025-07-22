from dataclasses import dataclass, field
from typing import List, Dict
import re
from datetime import datetime

@dataclass
class User:
    id: int
    email: str
    password: str
    balance: float = 0.0
    is_admin: bool = False
    history: List['Prediction'] = field(default_factory=list)
    transactions: List['Transaction'] = field(default_factory=list)

    def __post_init__(self):
        self._validate_email()
        self._validate_password()

    def _validate_email(self):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', self.email):
            raise ValueError("Некорректный email")

    def _validate_password(self):
        if len(self.password) < 8: # Простая проверка для примера, надо бы усложнить потом
            raise ValueError("Пароль должен содержать минимум 8 символов")

    def add_prediction(self, prediction: 'Prediction'):
        self.history.append(prediction)

    def add_transaction(self, transaction: 'Transaction'):
        self.transactions.append(transaction)
        self.balance += transaction.amount

@dataclass
class Movie:
    id: int
    title: str
    description: str
    image_url: str

    def __post_init__(self):
        self._validate_title()
        self._validate_description()

    def _validate_title(self):
        if len(self.title) < 1:
            raise ValueError("Название фильма должно быть не короче одного символа")

    def _validate_description(self):
        if len(self.description) < 10:
            raise ValueError("Описание фильма не должно быть короче 10 символов")
    
    def change_description(self, new_description):
        self.description = new_description # На случай каких то ошибок в описании
        
    def change_title(self, new_title):
        self.title = new_title # На случай каких то ошибок в названии

@dataclass
class Prediction:
    id: int
    user_id: int
    input_text: str
    results: List[Movie] = field(default_factory=list)
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    is_success: bool = True
    error_message: str = ""

@dataclass
class Transaction:
    id: int
    user_id: int
    amount: float  # положительное - пополнение, отрицательное - списание
    type: str  # "deposit", "prediction", "admin_adjustment"
    description: str
    timestamp: datetime = field(default_factory=datetime.now)

class MovieService:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.movies: Dict[int, Movie] = {}
        self._load_sample_data()
        self.prediction_cost = 5.0  # Стоимость одного запроса

    def _load_sample_data(self):
        # Пример фильмов
        self.movies[1] = Movie(1, "Интерстеллар", "Фантастика о космических путешествиях", "interstellar.jpg")
        self.movies[2] = Movie(2, "Начало", "Фильм о снах и реальности", "inception.jpg")

        # Тестовый админ
        admin = User(1, "admin@service.com", "securepassword", is_admin=True)
        admin.balance = 1000.0
        self.users[1] = admin

    def register_user(self, email: str, password: str) -> User:
        """Регистрация нового пользователя"""
        user_id = max(self.users.keys(), default=0) + 1
        user = User(user_id, email, password)
        self.users[user_id] = user
        
        # Добавляем стартовый бонус
        bonus = Transaction(
            id=1,
            user_id=user_id,
            amount=10.0,
            type="deposit",
            description="Приветственный бонус при регистрации"
        )
        user.add_transaction(bonus)
        
        return user

    def add_funds(self, user_id: int, amount: float) -> Transaction:
        """Пополнение баланса пользователем"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        transaction = Transaction(
            id=len(user.transactions) + 1,
            user_id=user_id,
            amount=amount,
            type="deposit",
            description="Пополнение баланса"
        )
        user.add_transaction(transaction)
        return transaction

    def admin_adjust_balance(self, admin_id: int, user_id: int, amount: float) -> Transaction:
        """Административное изменение баланса"""
        admin = self.users.get(admin_id)
        user = self.users.get(user_id)
        
        if not admin or not admin.is_admin:
            raise PermissionError("Требуются права администратора")
        if not user:
            raise ValueError("Пользователь не найден")
        
        transaction = Transaction(
            id=len(user.transactions) + 1,
            user_id=user_id,
            amount=amount,
            type="admin_adjustment",
            description=f"Корректировка администратором #{admin_id}"
        )
        user.add_transaction(transaction)
        return transaction

    def get_user_history(self, user_id: int) -> List[Prediction]:
        """Получение истории запросов пользователя"""
        user = self.users.get(user_id)
        return user.history if user else []

    def recommend_movies(self, user_id: int, text: str) -> Prediction:
        """Получение рекомендаций с валидацией и списанием средств"""

        # Проверка наличия юзера с таким id
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Валидация промта
        if len(text) < 10:
            prediction = Prediction(
                id=len(user.history) + 1,
                user_id=user_id,
                input_text=text,
                cost=0.0,
                is_success=False,
                error_message="Текст слишком короткий (мин. 10 символов)"
            )
            user.add_prediction(prediction)
            return prediction
        
        # Проверка баланса
        if user.balance < self.prediction_cost and not user.is_admin:
            raise ValueError("Недостаточно средств на балансе")
        
        # Создание записи о запросе
        prediction = Prediction(
            id=len(user.history) + 1,
            user_id=user_id,
            input_text=text,
            cost=self.prediction_cost
        )
        
        try:
            # Имитация работы ML-модели
            prediction.results = list(self.movies.values())[:3]
            
            # Списание средств (если не админ)
            if not user.is_admin:
                transaction = Transaction(
                    id=len(user.transactions) + 1,
                    user_id=user_id,
                    amount=-self.prediction_cost,
                    type="prediction",
                    description=f"Запрос рекомендаций #{prediction.id}"
                )
                user.add_transaction(transaction)
                
        except Exception as e:
            prediction.is_success = False
            prediction.error_message = str(e)
        
        user.add_prediction(prediction)
        return prediction