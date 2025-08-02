from typing import List, Optional
import bcrypt
from services.crud.recommender import MovieRecommender
from models.user import User
from models.wallet import Wallet
from models.movie import Movie
from models.transaction import Transaction
from models.prediction import Prediction
from database.database import engine
from sqlmodel import Session, select
from models.constants import TransactionType, TransactionCost
from services.crud.wallet import make_transaction


class MovieService:
    """
    Класс для представления функциональности самого сервиса.
    
    Attributes:
        recomender (Optional[MovieRecommender]): Опционально, добавляется класс модели с возможностью предсказания
    """
    def __init__(self):
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
        # self._setup_recommender()
        
        print("База данных инициализирована успешно!")

    def _create_demo_users(self) -> None:
        """Создание демо пользователей"""
        with Session(engine) as session:
            # Проверяем, существуют ли уже пользователи
            existing_users = session.exec(select(User)).first()
            if existing_users:
                print("Демо данные уже существуют")
                return
            
            # Создаем кошельки для пользователей
            user_wallet = Wallet()
            admin_wallet = Wallet()
            session.add(user_wallet)
            session.add(admin_wallet)
            session.commit()
            session.refresh(user_wallet)
            session.refresh(admin_wallet)
            
            # Создаем демо пользователя
            user_password_hash = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            demo_user = User(
                email="user@example.com",
                password_hash=user_password_hash,
                is_admin=False,
                wallet_id=user_wallet.id
            )
            session.add(demo_user)
            
            # Создаем демо администратора
            admin_password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            demo_admin = User(
                email="admin@example.com",
                password_hash=admin_password_hash,
                is_admin=True,
                wallet_id=admin_wallet.id
            )
            session.add(demo_admin)
            
            # Добавляем стартовые бонусы
            user_bonus = Transaction(
                user_id=demo_user.id,
                wallet_id=user_wallet.id,
                amount=TransactionCost.BONUS.value,
                type=TransactionType.DEPOSIT,
                description="Приветственный бонус при регистрации"
            )
            admin_bonus = Transaction(
                user_id=demo_admin.id,
                wallet_id=admin_wallet.id,
                amount=TransactionCost.BONUS.value,
                type=TransactionType.DEPOSIT,
                description="Приветственный бонус при регистрации"
            )
            make_transaction(user_wallet, user_bonus)
            make_transaction(admin_wallet, admin_bonus)
            
            session.add(user_bonus)
            session.add(admin_bonus)
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
        # Проверка, что пользователь с таким email еще не существует
        with Session(engine) as session:
            if session.exec(select(User).where(User.email == email)).first():
                raise ValueError("Пользователь с таким email уже существует")
            
            # Создаем кошелек для пользователя
            wallet = Wallet()
            session.add(wallet)
            session.commit()
            session.refresh(wallet)

            # Создаем пользователя
            password_hash = self._hash_password(password)
            user = User(
                email=email,
                password_hash=password_hash,
                wallet_id=wallet.id
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Добавляем стартовый бонус
            bonus = Transaction(
                user_id=user.id,
                wallet_id=user.wallet_id,
                amount=TransactionCost.BONUS.value,
                type=TransactionType.DEPOSIT,
                description="Приветственный бонус при регистрации"
            )
            make_transaction(user.wallet, bonus)
            
            # Добавляем транзакцию в сессию и коммитим
            session.add(bonus)
            session.commit()
            
            return user

    def add_funds(self, user_id: int, amount: float) -> Transaction:
        """Пополнение баланса пользователем"""
        with Session(engine) as session:
            user = self.users.get(user_id)
            if not user:
                raise ValueError("Пользователь не найден")
            
            transaction = Transaction(
                user_id=user.id,
                wallet_id=user.wallet_id,
                amount=TransactionCost(amount).value,
                type=TransactionType.DEPOSIT,
                description="Пополнение баланса"
            )
            make_transaction(user.wallet, transaction)
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def admin_adjust_balance(self, admin_user_id: int, target_user_id: int, amount: float) -> Transaction:
        """Административное изменение баланса"""
        with Session(engine) as session:
            # Получаем администратора
            admin_user = session.get(User, admin_user_id)
            if not admin_user:
                raise ValueError("Администратор не найден")
            if not admin_user.is_admin:
                raise PermissionError("Требуются права администратора")
            
            # Получаем целевого пользователя
            target_user = session.get(User, target_user_id)
            if not target_user:
                raise ValueError("Пользователь не найден")
            
            # Создаем транзакцию
            transaction = Transaction(
                user_id=target_user.id,
                wallet_id=target_user.wallet_id,
                amount=TransactionCost(amount),
                type=TransactionType.ADMIN_ADJUSTMENT,
                description=f"Корректировка администратором #{admin_user.id}"
            )
            make_transaction(target_user.wallet, transaction)
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def get_user_predictions_history(self, user_id: int) -> List[Prediction]:
        """Получение истории запросов пользователя"""
        with Session(engine) as session:
            # Получаем пользователя
            user = session.get(User, user_id)
            if not user:
                raise ValueError("Пользователь не найден")
            
            # Получаем текущего пользователя (для проверки прав)
            current_user = session.get(User, user_id)
            
            # Проверяем права доступа
            if current_user and (current_user.is_admin or current_user.id == user.id):
                # Получаем историю предсказаний пользователя
                predictions = session.exec(select(Prediction).where(Prediction.user_id == user.id)).all()
                return predictions
            else:
                raise PermissionError("Требуются права администратора")

    def get_user_transactions_history(self, user_id: int) -> List[Transaction]:
        """Получение истории транзакций пользователя"""
        with Session(engine) as session:
            # Получаем пользователя
            user = session.get(User, user_id)
            if not user:
                raise ValueError("Пользователь не найден")
            
            # Получаем текущего пользователя (для проверки прав)
            current_user = session.get(User, user_id)
            
            # Проверяем права доступа
            if current_user and (current_user.is_admin or current_user.id == user.id):
                # Получаем историю транзакций пользователя
                transactions = session.exec(select(Transaction).where(Transaction.user_id == user.id)).all()
                return transactions
            else:
                raise PermissionError("Требуются права администратора")

    def recommend_movies(self, user_id: int, input_text: str) -> Prediction:
        """Получение рекомендаций с валидацией и списанием средств"""
        # Проверка наличия юзера
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        # Списание средств
        if user.wallet.balance < TransactionCost.BASIC.value:
            raise ValueError("Недостаточно средств для получения рекомендаций")
        
        # Загрузка модели
        self.ml_model = self.recomender(list(self.movies.values()))
        if not self.ml_model:
            raise ValueError("ML модель не инициализирована")
        
        # Полуение рекомендаций
        model_prediction = self.ml_model.predict(user, input_text)
        if len(model_prediction) == 0:
            raise ValueError("Получен пустой список рекомендаций")
        
        # Определяем стоимость
        cost = TransactionCost.ADMIN.value if user.is_admin else TransactionCost.BASIC.value
        
        prediction = Prediction(
            id=len(user.prediction_history.predictions) + 1,
            user_id=user.id,
            input_text=input_text,
            cost=cost,
            results=model_prediction,
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
        with Session(engine) as session:
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            
            # Создаем связи с фильмами через PredictionMovieLink
            from models.prediction import PredictionMovieLink
            for movie in model_prediction:
                link = PredictionMovieLink(
                    prediction_id=prediction.id,
                    movie_id=movie.id
                )
                session.add(link)
            session.commit()
        
        return prediction
