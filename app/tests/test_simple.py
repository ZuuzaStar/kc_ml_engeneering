import pytest
from fastapi.testclient import TestClient
import json


def test_health_check(client):
    """Тест health check эндпоинта"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_mock_user_creation(mock_user):
    """Тест создания мок пользователя"""
    assert mock_user.email == "test@example.com"
    assert mock_user.is_admin is False
    assert hasattr(mock_user, 'wallet')
    assert mock_user.wallet.balance == 100.0


def test_mock_admin_user_creation(mock_admin_user):
    """Тест создания мок админа"""
    assert mock_admin_user.email == "admin@example.com"
    assert mock_admin_user.is_admin is True
    assert mock_admin_user.wallet.balance == 1000.0


def test_mock_movie_creation(mock_movie):
    """Тест создания мок фильма"""
    assert mock_movie.title == "Test Movie"
    assert mock_movie.year == 2023
    
    # Проверяем что жанры сохранены как JSON строка
    genres = json.loads(mock_movie.genres)
    assert genres == ["action", "drama"]
    
    # Проверяем что embedding сохранен как JSON строка
    embedding = json.loads(mock_movie.embedding)
    assert len(embedding) == 384


def test_mock_transaction_creation(mock_transaction):
    """Тест создания мок транзакции"""
    assert mock_transaction.amount == 50.0
    assert mock_transaction.type == "DEPOSIT"
    assert mock_transaction.description == "Test deposit"


def test_mock_prediction_creation(mock_prediction):
    """Тест создания мок предсказания"""
    assert mock_prediction.input_text == "I want to watch an action movie"
    assert mock_prediction.cost == 1.0
    
    # Проверяем что embedding сохранен как JSON строка
    embedding = json.loads(mock_prediction.embedding)
    assert len(embedding) == 384

def test_mock_movie_data_fixture(mock_movie_data):
    """Тест фикстуры mock_movie_data"""
    # Проверяем структуру данных
    assert "title" in mock_movie_data
    assert "description" in mock_movie_data
    assert "year" in mock_movie_data
    assert "genres" in mock_movie_data
    assert "embedding" in mock_movie_data
    
    # Проверяем конкретные значения
    assert mock_movie_data["title"] == "Test Movie"
    assert mock_movie_data["year"] == 2023
    assert mock_movie_data["genres"] == ["action", "drama"]
    assert len(mock_movie_data["embedding"]) == 384
