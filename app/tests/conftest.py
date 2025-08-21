import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlmodel import SQLModel, Session, create_engine 
from sqlalchemy.pool import StaticPool
import bcrypt
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Создаем базовый класс для тестовых моделей
Base = declarative_base()

# Упрощенные тестовые модели для SQLite
class TestUser(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)

class TestWallet(Base):
    __tablename__ = "wallet"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True)
    balance = Column(Float, default=0.0)

class TestTransaction(Base):
    __tablename__ = "transaction"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    wallet_id = Column(Integer, index=True)
    amount = Column(Float, default=0.0)
    type = Column(String)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TestMovie(Base):
    __tablename__ = "movie"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, unique=True)
    year = Column(Integer)
    genres = Column(Text)  # JSON строка для эмуляции ARRAY
    embedding = Column(Text)  # JSON строка для эмуляции Vector
    timestamp = Column(DateTime, default=datetime.utcnow)

class TestPrediction(Base):
    __tablename__ = "prediction"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    input_text = Column(Text)
    embedding = Column(Text)  # JSON строка для эмуляции Vector
    cost = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Создаем простое тестовое приложение без Telegram бота
def create_test_app():
    app = FastAPI()
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app

@pytest.fixture(name="session")  
def session_fixture():  
    engine = create_engine("sqlite:///testing.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client") 
def client_fixture(session: Session):  
    app = create_test_app()
    client = TestClient(app)  
    yield client  

@pytest.fixture
def mock_user_data():
    """Тестовые данные пользователя"""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
        "is_admin": False
    }

@pytest.fixture
def mock_user(session, mock_user_data):
    """Создает тестового пользователя в базе"""
    # Хешируем пароль
    password_hash = bcrypt.hashpw(
        mock_user_data["password"].encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")
    
    user = TestUser(
        email=mock_user_data["email"],
        password_hash=password_hash,
        is_admin=mock_user_data["is_admin"]
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Создаем кошелек для пользователя
    wallet = TestWallet(user_id=user.id, balance=100.0)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    
    # Добавляем атрибут wallet для совместимости с тестами
    user.wallet = wallet
    
    return user

@pytest.fixture
def mock_admin_user(session):
    """Создает тестового админа"""
    password_hash = bcrypt.hashpw(
        "AdminPass123".encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")
    
    user = TestUser(
        email="admin@example.com",
        password_hash=password_hash,
        is_admin=True
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    wallet = TestWallet(user_id=user.id, balance=1000.0)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    
    # Добавляем атрибут wallet для совместимости с тестами
    user.wallet = wallet
    
    return user

@pytest.fixture
def mock_movie_data():
    """Тестовые данные фильма"""
    return {
        "title": "Test Movie",
        "description": "A test movie for testing purposes",
        "year": 2023,
        "genres": ["action", "drama"],  # Оригинальный ARRAY для теста
        "embedding": [0.1] * 384  # Оригинальный Vector для теста
    }

@pytest.fixture
def mock_movie(session, mock_movie_data):
    """Создает тестовый фильм в базе"""
    import json
    
    movie = TestMovie(
        title=mock_movie_data["title"],
        description=mock_movie_data["description"],
        year=mock_movie_data["year"],
        genres=json.dumps(mock_movie_data["genres"]),  # Сохраняем как JSON строку
        embedding=json.dumps(mock_movie_data["embedding"])  # Сохраняем как JSON строку
    )
    
    session.add(movie)
    session.commit()
    session.refresh(movie)
    
    return movie

@pytest.fixture
def mock_transaction(session, mock_user):
    """Создает тестовую транзакцию"""
    transaction = TestTransaction(
        user_id=mock_user.id,
        wallet_id=mock_user.wallet.id,
        amount=50.0,
        type="DEPOSIT",
        description="Test deposit"
    )
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    # Добавляем атрибут transactions для совместимости с тестами
    if not hasattr(mock_user.wallet, 'transactions'):
        mock_user.wallet.transactions = []
    mock_user.wallet.transactions.append(transaction)
    
    return transaction

@pytest.fixture
def mock_prediction(session, mock_user, mock_movie):
    """Создает тестовое предсказание"""
    import json
    
    prediction = TestPrediction(
        user_id=mock_user.id,
        input_text="I want to watch an action movie",
        embedding=json.dumps([0.1] * 384),  # Сохраняем как JSON строку
        cost=1.0
    )
    
    session.add(prediction)
    session.commit()
    session.refresh(prediction)
    
    # Добавляем атрибут predictions для совместимости с тестами
    if not hasattr(mock_user, 'predictions'):
        mock_user.predictions = []
    mock_user.predictions.append(prediction)
    
    return prediction