import pytest
from fastapi.testclient import TestClient
import bcrypt


class TestUserOperations:
    """Тесты для операций с пользователями"""
    
    def test_user_model_creation(self, mock_user):
        """Тест создания модели пользователя"""
        assert mock_user.email == "test@example.com"
        assert mock_user.is_admin is False
        assert hasattr(mock_user, 'wallet')
        assert mock_user.wallet.balance == 0.0
    
    def test_user_password_hashing(self, mock_user_data):
        """Тест хеширования пароля пользователя"""
        password = mock_user_data["password"]
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        
        # Проверяем что пароль можно проверить
        assert bcrypt.checkpw(password.encode("utf-8"), password_hash)
        assert not bcrypt.checkpw("wrong_password".encode("utf-8"), password_hash)
    
    def test_admin_user_creation(self, mock_admin_user):
        """Тест создания пользователя администратора"""
        assert mock_admin_user.email == "admin@example.com"
        assert mock_admin_user.is_admin is True
        assert mock_admin_user.wallet.balance == 1000.0
    
    def test_user_data_validation(self, mock_user_data):
        """Тест валидации данных пользователя"""
        # Проверяем что данные содержат необходимые поля
        assert "email" in mock_user_data
        assert "password" in mock_user_data
        assert "is_admin" in mock_user_data
        
        # Проверяем типы данных
        assert isinstance(mock_user_data["email"], str)
        assert isinstance(mock_user_data["password"], str)
        assert isinstance(mock_user_data["is_admin"], bool)
    
    def test_user_wallet_relationship(self, mock_user):
        """Тест связи пользователя с кошельком"""
        assert hasattr(mock_user, 'wallet')
        assert mock_user.wallet.user_id == mock_user.id
    
    def test_email_uniqueness_logic(self, mock_user, mock_admin_user):
        """Тест уникальности email адресов"""
        # Проверяем что у пользователей разные email
        assert mock_user.email != mock_admin_user.email
    
    def test_user_transaction_capability(self, mock_user, mock_transaction):
        """Тест способности пользователя создавать транзакции"""
        # Проверяем что пользователь может иметь транзакции
        assert mock_transaction.user_id == mock_user.id
    
    def test_user_wallet_transaction_chain(self, mock_user, mock_transaction):
        """Тест цепочки связей: пользователь -> кошелек -> транзакция"""
        # Проверяем полную цепочку связей
        assert mock_user.id == mock_transaction.user_id
        assert mock_user.wallet.id == mock_transaction.wallet_id
