from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional

class UserType(Enum):
    REGULAR = "regular"
    ADMIN = "admin"

class BaseEntity:
    def __init__(self, id: int):
        self._id = id

    @property
    def id(self) -> int:
        return self._id

class User(BaseEntity):
    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        password_hash: str,
        balance: float = 0.0,
        user_type: UserType = UserType.REGULAR
    ):
        super().__init__(id)
        self._username = username
        self._email = email
        self._password_hash = password_hash
        self._balance = balance
        self._user_type = user_type

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def user_type(self) -> UserType:
        return self._user_type

    def check_password(self, password: str) -> bool:
        # Логика проверки пароля
        pass

    def update_balance(self, amount: float):
        self._balance += amount

class MLModel(BaseEntity):
    def __init__(
        self,
        id: int,
        name: str,
        version: str,
        cost: float,
        description: str = ""
    ):
        super().__init__(id)
        self._name = name
        self._version = version
        self._cost = cost
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def cost(self) -> float:
        return self._cost

    def predict(self, input_data: str) -> List[Dict]:
        # Логика предсказания с использованием ML
        pass

class TransactionType(Enum):
    REPLENISH = "replenish"
    PREDICTION = "prediction"
    ADMIN_OPERATION = "admin_operation"

class Transaction(BaseEntity):
    def __init__(
        self,
        id: int,
        user_id: int,
        amount: float,
        transaction_type: TransactionType,
        description: str = "",
        timestamp: datetime = datetime.now()
    ):
        super().__init__(id)
        self._user_id = user_id
        self._amount = amount
        self._transaction_type = transaction_type
        self._description = description
        self._timestamp = timestamp

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def transaction_type(self) -> TransactionType:
        return self._transaction_type

class PredictionResult(BaseEntity):
    def __init__(
        self,
        id: int,
        user_id: int,
        model_id: int,
        input_data: str,
        result: List[Dict],
        transaction_id: int
    ):
        super().__init__(id)
        self._user_id = user_id
        self._model_id = model_id
        self._input_data = input_data
        self._result = result
        self._transaction_id = transaction_id

    @property
    def input_data(self) -> str:
        return self._input_data

    @property
    def result(self) -> List[Dict]:
        return self._result

    @property
    def transaction_id(self) -> int:
        return self._transaction_id

class Validator(ABC):
    @abstractmethod
    def validate(self, data: str) -> bool:
        pass

class MovieDescriptionValidator(Validator):
    def validate(self, data: str) -> bool:
        # Логика валидации текстового описания
        return len(data) > 10 and len(data) < 1000

class BalanceManager:
    def __init__(self, transaction_history: List[Transaction] = []):
        self._transaction_history = transaction_history

    def replenish_balance(self, user: User, amount: float) -> Transaction:
        user.update_balance(amount)
        transaction = Transaction(
            id=len(self._transaction_history) + 1,
            user_id=user.id,
            amount=amount,
            transaction_type=TransactionType.REPLENISH
        )
        self._transaction_history.append(transaction)
        return transaction

    def withdraw_balance(self, user: User, amount: float) -> Optional[Transaction]:
        if user.balance >= amount:
            user.update_balance(-amount)
            transaction = Transaction(
                id=len(self._transaction_history) + 1,
                user_id=user.id,
                amount=-amount,
                transaction_type=TransactionType.PREDICTION
            )
            self._transaction_history.append(transaction)
            return transaction
        return None

class PredictionManager:
    def __init__(
        self,
        ml_model: MLModel,
        validator: Validator,
        balance_manager: BalanceManager
    ):
        self._ml_model = ml_model
        self._validator = validator
        self._balance_manager = balance_manager

    def make_prediction(self, user: User, input_data: str) -> Optional[PredictionResult]:
        if not self._validator.validate(input_data):
            return None
        
        transaction = self._balance_manager.withdraw_balance(user, self._ml_model.cost)
        if not transaction:
            return None
        
        result = self._ml_model.predict(input_data)
        return PredictionResult(
            id=len(prediction_history) + 1,
            user_id=user.id,
            model_id=self._ml_model.id,
            input_data=input_data,
            result=result,
            transaction_id=transaction.id
        )

class AdminUser(User):
    def replenish_user_balance(
        self,
        user: User,
        amount: float,
        balance_manager: BalanceManager
    ) -> Transaction:
        transaction = balance_manager.replenish_balance(user, amount)
        transaction._transaction_type = TransactionType.ADMIN_OPERATION
        return transaction

# Пример использования
if __name__ == "__main__":
    # Инициализация компонентов
    validator = MovieDescriptionValidator()
    model = MLModel(1, "MovieRecommender", "v1.0", 5.0)
    transactions = []
    balance_manager = BalanceManager(transactions)
    prediction_manager = PredictionManager(model, validator, balance_manager)
    prediction_history = []

    # Создание пользователей
    user = User(1, "john_doe", "john@example.com", "hash123", 100.0)
    admin = AdminUser(2, "admin", "admin@example.com", "admin_hash", 0, UserType.ADMIN)

    # Пополнение баланса
    balance_manager.replenish_balance(user, 50.0)

    # Выполнение предсказания
    prediction = prediction_manager.make_prediction(
        user,
        "Комедийный фильм о группе друзей, путешествующих по Европе"
    )
    
    if prediction:
        prediction_history.append(prediction)
        print("Recommendations:", prediction.result)
        print("New balance:", user.balance)
    else:
        print("Prediction failed")