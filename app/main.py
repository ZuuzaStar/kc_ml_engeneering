from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
import bcrypt
from models.recommender import MovieRecommender
from models.user import User, Admin
from models.movie import Movie
from models.transaction import Transaction
from models.prediction import Prediction
from database.database import engine
from sqlmodel import Session, select

load_dotenv() # Загружаем глобальные переменные

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

    def initialize_database(self) -> None:
        """
        Инициализация базы данных стандартными данными:
        - Демо пользователь
        - Демо администратор  
        - Базовые фильмы
        """
        print("Инициализация базы данных...")
        
        # Создаем демо данные
        self._create_demo_users()
        self._create_demo_movies()
        self._setup_recommender()
        
        print("База данных инициализирована успешно!")

    def _create_demo_users(self) -> None:
        """Создание демо пользователей"""
        with Session(engine) as session:
            # Проверяем, существуют ли уже пользователи
            existing_users = session.exec(select(User)).first()
            if existing_users:
                print("Демо данные уже существуют")
                return
            
            # Создаем демо пользователя
            user_password_hash = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            demo_user = User(
                email="user@example.com",
                password_hash=user_password_hash,
                is_admin=False,
                balance=100.0
            )
            session.add(demo_user)
            
            # Создаем демо администратора
            admin_password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            demo_admin = Admin(
                email="admin@example.com",
                password_hash=admin_password_hash,
                is_admin=True,
                balance=1000.0
            )
            session.add(demo_admin)
            
            session.commit()
            print("Демо пользователи созданы")

    def _create_demo_movies(self) -> None:
        """Создание демо фильмов"""
        demo_movies_data = [
            {
                "title": "The Matrix",
                "description": "Компьютерный хакер Нео узнает о шокирующей правде: все, что он считал реальностью, является всего лишь Иллюзией.",
                "cover_image_url": "https://example.com/matrix.jpg"
            },
            {
                "title": "Inception",
                "description": "Профессионал по проникновению в сны получает новое задание:植入 и извлечение идеи из подсознания.",
                "cover_image_url": "https://example.com/inception.jpg"
            },
            {
                "title": "Interstellar",
                "description": "Ученый Купер решает отправиться в путешествие, чтобы спасти человечество от вымирания.",
                "cover_image_url": "https://example.com/interstellar.jpg"
            },
            {
                "title": "The Dark Knight",
                "description": "Бэтмен сталкивается со сложным выбором между анархией и порядком, когда Джокер устраивает хаос в Готэме.",
                "cover_image_url": "https://example.com/darkknight.jpg"
            },
            {
                "title": "Pulp Fiction",
                "description": "Несколько связанных историй о мафии, боксерах и гангстерах в стиле нелинейного повествования.",
                "cover_image_url": "https://example.com/pulpfiction.jpg"
            }
        ]
        
        with Session(engine) as session:
            # Проверяем, существуют ли уже фильмы
            existing_movies = session.exec(select(Movie)).first()
            if existing_movies:
                print("Демо фильмы уже существуют")
                return
            
            # Создаем демо фильмы
            for movie_data in demo_movies_data:
                movie = Movie(**movie_data)
                session.add(movie)
            
            session.commit()
            print(f"Создано {len(demo_movies_data)} демо фильмов")

    def _setup_recommender(self) -> None:
        """Настройка рекомендательной системы"""
        with Session(engine) as session:
            # Получаем все фильмы из базы
            movies = session.exec(select(Movie)).all()
            if movies:
                self.recomender = MovieRecommender(movies)
                print("Рекомендательная система инициализирована")
            else:
                print("Нет фильмов для рекомендательной системы")

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
                cost=float(os.getenv("PREDICTION_COST", 10)),
                is_success=False,
                error_code=1
            )

        # Проверка баланса и создание записи о запросе
        if user.wallet.balance < float(os.getenv("PREDICTION_COST", 10)) and not user.is_admin:
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
                    amount=-float(os.getenv("PREDICTION_COST", 10)),
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