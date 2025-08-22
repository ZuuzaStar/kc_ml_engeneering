"""
Конфигурация pytest для тестов
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine
import json
from datetime import datetime
import bcrypt

# Импортируем тестовые модели из простой фабрики
from tests.simple_factory import TestUser, TestWallet, TestTransaction, TestMovie, TestPrediction


def create_test_app():
    """Создает минимальное тестовое FastAPI приложение"""
    app = FastAPI()
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


@pytest.fixture(name="session")
def session_fixture():
    """Фикстура для создания тестовой сессии БД"""
    engine = create_engine(
        "sqlite:///testing.db", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    
    # Удаляем и создаем таблицы заново для каждого теста
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture():
    """Фикстура для создания тестового клиента"""
    app = create_test_app()
    return TestClient(app)


@pytest.fixture(name="db_session")
def db_session_fixture(session):
    """Фикстура для работы с БД в тестах"""
    return session


# Фикстуры с тестовыми данными
@pytest.fixture(name="mock_user_data")
def mock_user_data_fixture():
    """Тестовые данные пользователя"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "is_admin": False
    }


@pytest.fixture(name="mock_user")
def mock_user_fixture(db_session, mock_user_data):
    """Создает тестового пользователя в БД"""
    # Хешируем пароль
    password_hash = bcrypt.hashpw(
        mock_user_data["password"].encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")
    
    # Создаем пользователя
    user = TestUser(
        email=mock_user_data["email"],
        password_hash=password_hash,
        is_admin=mock_user_data["is_admin"]
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Создаем кошелек для пользователя
    wallet = TestWallet(user_id=user.id, balance=0.0)
    db_session.add(wallet)
    db_session.commit()
    db_session.refresh(wallet)
    
    # Привязываем кошелек к пользователю (только в памяти для тестов)
    object.__setattr__(user, 'wallet', wallet)
    object.__setattr__(user, 'transactions', [])
    object.__setattr__(user, 'predictions', [])
    
    return user


@pytest.fixture(name="mock_admin_user")
def mock_admin_user_fixture(db_session, mock_user_data):
    """Создает тестового админа в БД"""
    # Хешируем пароль
    password_hash = bcrypt.hashpw(
        mock_user_data["password"].encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")
    
    # Создаем админа
    admin_user = TestUser(
        email="admin@example.com",
        password_hash=password_hash,
        is_admin=True
    )
    
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    
    # Создаем кошелек для админа
    wallet = TestWallet(user_id=admin_user.id, balance=1000.0)
    db_session.add(wallet)
    db_session.commit()
    db_session.refresh(wallet)
    
    # Привязываем кошелек к админу (только в памяти для тестов)
    object.__setattr__(admin_user, 'wallet', wallet)
    object.__setattr__(admin_user, 'transactions', [])
    object.__setattr__(admin_user, 'predictions', [])
    
    return admin_user


@pytest.fixture(name="mock_movie_data")
def mock_movie_data_fixture():
    """Тестовые данные фильма"""
    return {
        "title": "Test Movie",
        "description": "A test movie for testing purposes",
        "year": 2023,
        "genres": ["action", "drama"],
        "embedding": [0.1, 0.2, 0.3, 0.4] * 96  # 384-мерный вектор
    }


@pytest.fixture(name="mock_movie")
def mock_movie_fixture(db_session, mock_movie_data):
    """Создает тестовый фильм в БД"""
    # Используем простую фабрику, которая автоматически преобразует типы
    movie = TestMovie(
        title=mock_movie_data["title"],
        description=mock_movie_data["description"],
        year=mock_movie_data["year"],
        genres=mock_movie_data["genres"],  # Автоматически преобразуется в JSON
        embedding=mock_movie_data["embedding"]  # Автоматически преобразуется в JSON
    )
    
    db_session.add(movie)
    db_session.commit()
    db_session.refresh(movie)
    
    return movie


@pytest.fixture(name="mock_transaction")
def mock_transaction_fixture(db_session, mock_user):
    """Создает тестовую транзакцию в БД"""
    transaction = TestTransaction(
        user_id=mock_user.id,
        wallet_id=mock_user.wallet.id,
        amount=100.0,
        type="DEPOSIT",
        description="Test deposit transaction"
    )
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    return transaction


@pytest.fixture(name="mock_prediction")
def mock_prediction_fixture(db_session, mock_user):
    """Создает тестовое предсказание в БД"""
    prediction = TestPrediction(
        user_id=mock_user.id,
        input_text="I want to watch an action movie",
        embedding=[0.1, 0.2, 0.3, 0.4] * 96,  # Автоматически преобразуется в JSON
        cost=5.0
    )
    
    db_session.add(prediction)
    db_session.commit()
    db_session.refresh(prediction)
    
    return prediction