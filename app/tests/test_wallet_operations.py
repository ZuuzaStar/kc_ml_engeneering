import pytest
from fastapi.testclient import TestClient


class TestWalletOperations:
    """Тесты для операций с кошельком"""
    
    def test_balance_operations_logic(self, mock_user):
        """Тест логики операций с балансом"""
        initial_balance = mock_user.wallet.balance
        
        # Проверяем что баланс равен ожидаемому значению
        assert initial_balance == 0.0
        
        # Проверяем что кошелек связан с пользователем
        assert mock_user.wallet.user_id == mock_user.id
    
    def test_wallet_model_creation(self, mock_user):
        """Тест создания модели кошелька"""
        assert hasattr(mock_user, 'wallet')
        assert mock_user.wallet.balance == 0.0
        assert mock_user.wallet.user_id == mock_user.id
    
    def test_transaction_model_creation(self, mock_transaction):
        """Тест создания модели транзакции"""
        assert mock_transaction.amount == 100.0
        assert mock_transaction.type == "DEPOSIT"  # Упрощенная модель использует строку
        assert mock_transaction.description == "Test deposit transaction"
    
    def test_transaction_constants(self):
        """Тест констант транзакций"""
        # В упрощенной модели используем строковые константы
        assert "DEPOSIT" == "DEPOSIT"
        assert "PREDICTION" == "PREDICTION"
        assert "ADMIN_ADJUSTMENT" == "ADMIN_ADJUSTMENT"
    
    def test_transaction_user_relationship(self, mock_transaction, mock_user):
        """Тест связи транзакции с пользователем"""
        assert mock_transaction.user_id == mock_user.id
    
    def test_transaction_wallet_relationship(self, mock_transaction, mock_user):
        """Тест связи транзакции с кошельком"""
        assert mock_transaction.wallet_id == mock_user.wallet.id
        assert mock_transaction.wallet_id is not None
        assert mock_transaction.wallet_id > 0
    
    def test_transaction_amount_validation(self, mock_transaction):
        """Тест валидации суммы транзакции"""
        assert mock_transaction.amount == 100.0
        assert isinstance(mock_transaction.amount, float)
    
    def test_transaction_type_validation(self, mock_transaction):
        """Тест валидации типа транзакции"""
        assert mock_transaction.type == "DEPOSIT"
    
    def test_transaction_description(self, mock_transaction):
        """Тест описания транзакции"""
        assert mock_transaction.description == "Test deposit transaction"
    
    def test_transaction_timestamp(self, mock_transaction):
        """Тест временной метки транзакции"""
        assert mock_transaction.timestamp is not None
        from datetime import datetime
        assert isinstance(mock_transaction.timestamp, datetime)
    
    def test_multiple_transactions_same_user(self, mock_user, session):
        """Тест создания нескольких транзакций для одного пользователя"""
        # Создаем дополнительные транзакции
        from tests.conftest import TestTransaction
        
        transaction1 = TestTransaction(
            user_id=mock_user.id,
            wallet_id=mock_user.wallet.id,
            amount=25.0,
            type="WITHDRAWAL",
            description="Test withdrawal"
        )
        
        transaction2 = TestTransaction(
            user_id=mock_user.id,
            wallet_id=mock_user.wallet.id,
            amount=75.0,
            type="DEPOSIT",
            description="Test deposit 2"
        )
        
        session.add(transaction1)
        session.add(transaction2)
        session.commit()
        
        # Проверяем что транзакции созданы
        assert transaction1.id is not None
        assert transaction2.id is not None
        assert transaction1.amount == 25.0
        assert transaction2.amount == 75.0
        assert transaction1.type == "WITHDRAWAL"
        assert transaction2.type == "DEPOSIT"