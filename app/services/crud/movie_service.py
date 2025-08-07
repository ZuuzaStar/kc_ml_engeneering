from typing import List, Optional
import bcrypt
from services.recommender import MovieRecommender
from models.user import User
from models.wallet import Wallet
from models.movie import Movie
from models.transaction import Transaction
from models.prediction import Prediction
from database.database import engine
from sqlmodel import Session, select
from models.constants import TransactionType, TransactionCost
from services.crud.wallet import make_transaction
from services.crud.user import hash_password


class MovieService:
    """
    Класс для представления функциональности самого сервиса.
    
    Attributes:
        recomender (Optional[MovieRecommender]): Опционально, добавляется класс модели с возможностью предсказания
    """
    def __init__(self):
        self.recomender: Optional[MovieRecommender] = None

    def initialize_demo_database(self, session: Session) -> None:
        """
        Инициализация базы данных стандартными данными:
        - Демо пользователь
        - Демо администратор  
        - Базовые фильмы
        """
        print("Инициализация базы данных...")
        
        # Создаем демо данные
        self._create_demo_users(session)
        self._create_demo_movies(session)
        self._setup_recommender(session)
        
        print("База данных инициализирована успешно!")

    def _create_demo_users(self, session: Session) -> None:
        """Создание демо пользователей"""
        # Проверяем, существуют ли уже пользователи
        existing_users = session.exec(select(User)).first()
        if existing_users:
            print("Демо данные уже существуют")
            return
        
        # Создаем демо пользователей
        demo_user = User(
            email="user@example.com",
            password_hash=hash_password("user123")
        )
        demo_admin = User(
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            is_admin=True,
        )
        # Создаем кошельки для пользователей
        demo_user.wallet = Wallet()
        demo_admin.wallet = Wallet()
        session.add(demo_user.wallet)
        session.add(demo_admin.wallet)
        session.refresh(demo_user.wallet)
        session.refresh(demo_admin.wallet)
        
        # Создаем демо пользователя
        session.add(demo_user)
        session.add(demo_admin)
                
        # Добавляем стартовые бонусы
        user_bonus = Transaction(
            user_id=demo_user.id,
            wallet_id=demo_user.wallet.id,
            amount=TransactionCost.BONUS.value,
            type=TransactionType.DEPOSIT,
            description="Приветственный бонус при регистрации"
        )
        admin_bonus = Transaction(
            user_id=demo_admin.id,
            wallet_id=demo_admin.wallet.id,
            amount=TransactionCost.BONUS.value,
            type=TransactionType.DEPOSIT,
            description="Приветственный бонус при регистрации"
        )
        make_transaction(demo_user.wallet, user_bonus)
        make_transaction(demo_admin.wallet, admin_bonus)
        
        session.add(user_bonus)
        session.add(admin_bonus)
        session.commit()
        print("Демо пользователи созданы")

    def _create_demo_movies(self, session: Session) -> None:
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

    def _setup_recommender(self, session: Session) -> None:
        """Настройка рекомендательной системы"""
        movies = session.exec(select(Movie)).all()
        if movies:
            self.recomender = MovieRecommender(movies)
            print("Рекомендательная система инициализирована")
        else:
            print("Нет фильмов для рекомендательной системы")

    def recommend_movies(self, user_id: int, input_text: str, session: Session) -> Prediction:
        """Получение рекомендаций с валидацией и списанием средств"""
        # Проверка наличия юзера
        user = session.get(User, user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        # Списание средств
        if user.wallet.balance < TransactionCost.BASIC.value:
            raise ValueError("Недостаточно средств для получения рекомендаций")
        
        # Загрузка модели
        # self._setup_recommender()
        self.ml_model = self.recomender(list(self.movies.values()))
        if not self.ml_model:
            raise ValueError("ML модель не инициализирована")
        
        # Полуение рекомендаций
        recommendations = self.ml_model.predict(user, input_text)
        if len(recommendations) == 0:
            raise ValueError("Получен пустой список рекомендаций")
        
        # Определяем стоимость
        cost = TransactionCost.ADMIN.value if user.is_admin else TransactionCost.BASIC.value
        
        prediction = Prediction(
            id=len(user.prediction_history.predictions) + 1,
            user_id=user.id,
            input_text=input_text,
            cost=cost,
            results=recommendations,
        )

        transaction = Transaction(
            id=len(user.wallet.transactions) + 1,
            user_id=user.id,
            wallet_id=user.wallet_id,
            amount=-cost,
            type=TransactionType.PREDICTION,
            description=f"Запрос рекомендаций #{prediction.id}"
        )
        
        make_transaction(user.wallet, transaction)
        # user.predictions.append(prediction)

        # Сохраняем в базу данных
        session.add(prediction)
        session.commit()
        session.refresh(prediction)
        
        # Создаем связи с фильмами через PredictionMovieLink
        from models.prediction import PredictionMovieLink
        for movie in recommendations:
            link = PredictionMovieLink(
                prediction_id=prediction.id,
                movie_id=movie.id
            )
            session.add(link)
        session.commit()
        
        return prediction
