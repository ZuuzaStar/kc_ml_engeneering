import pytest
from fastapi.testclient import TestClient
import json


class TestIntegrationScenarios:
    """Интеграционные тесты для проверки полных сценариев работы системы"""
    
    def test_test_application_works(self, client, session):
        """Тест работы тестового приложения"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
        
    def test_client_fixture_works(self, client):
        """Тест работы фикстуры клиента"""
        assert client is not None
        # Проверяем что неизвестный эндпоинт возвращает 404 (нормальное поведение)
        response = client.get("/unknown")
        assert response.status_code == 404
    
    def test_user_model_relationships(self, mock_user):
        """Тест связей модели пользователя"""
        assert hasattr(mock_user, 'wallet')
        assert mock_user.wallet is not None
        assert mock_user.wallet.user_id == mock_user.id
    
    def test_wallet_transaction_relationship(self, mock_transaction):
        """Тест связи кошелька и транзакций"""
        assert mock_transaction.user_id is not None
        assert mock_transaction.wallet_id is not None
        assert mock_transaction.amount == 100.0
    
    def test_movie_prediction_data_integrity(self, mock_movie, mock_prediction):
        """Тест целостности данных фильмов и предсказаний"""
        # Проверяем фильм
        assert mock_movie.title == "Test Movie"
        
        # Проверяем ARRAY поле (жанры)
        genres = json.loads(mock_movie.genres)
        assert isinstance(genres, list)
        assert len(genres) == 2
        
        # Проверяем Vector поле (embedding)
        embedding = json.loads(mock_movie.embedding)
        assert len(embedding) == 384
        
        # Проверяем предсказание
        assert mock_prediction.input_text == "I want to watch an action movie"
        pred_embedding = json.loads(mock_prediction.embedding)
        assert len(pred_embedding) == 384
        assert mock_prediction.cost > 0
    
    def test_admin_user_privileges(self, mock_admin_user):
        """Тест прав администратора"""
        assert mock_admin_user.is_admin is True
        assert mock_admin_user.wallet.balance == 1000.0
        assert mock_admin_user.email == "admin@example.com"
    
    def test_array_vector_field_operations(self, mock_movie, mock_prediction):
        """Тест операций с ARRAY и Vector полями"""
        # Тестируем операции с жанрами (ARRAY)
        genres = json.loads(mock_movie.genres)
        original_count = len(genres)
        
        # Добавляем новый жанр
        genres.append("thriller")
        mock_movie.genres = json.dumps(genres)
        updated_genres = json.loads(mock_movie.genres)
        assert len(updated_genres) == original_count + 1
        assert "thriller" in updated_genres
        
        # Тестируем операции с embedding (Vector)
        embedding = json.loads(mock_movie.embedding)
        
        # Изменяем embedding
        embedding[0] = 0.9
        mock_movie.embedding = json.dumps(embedding)
        updated_embedding = json.loads(mock_movie.embedding)
        assert updated_embedding[0] == 0.9
    
    def test_data_persistence_patterns(self, mock_movie, mock_prediction):
        """Тест паттернов сохранения данных для ARRAY и Vector"""
        # Проверяем что ARRAY поля сохраняются как JSON
        assert isinstance(mock_movie.genres, str)
        assert isinstance(mock_prediction.embedding, str)
        
        # Проверяем что можно восстановить данные
        try:
            genres = json.loads(mock_movie.genres)
            movie_embedding = json.loads(mock_movie.embedding)
            pred_embedding = json.loads(mock_prediction.embedding)
            
            assert isinstance(genres, list)
            assert isinstance(movie_embedding, list)
            assert isinstance(pred_embedding, list)
        except json.JSONDecodeError:
            pytest.fail("JSON поля должны корректно восстанавливаться")
    
    def test_model_consistency_across_operations(self, mock_user, mock_movie, mock_prediction):
        """Тест консистентности моделей при различных операциях"""
        # Проверяем что все модели имеют корректные типы данных
        assert isinstance(mock_user.id, int)
        assert isinstance(mock_user.email, str)
        assert isinstance(mock_user.wallet.balance, float)
        
        assert isinstance(mock_movie.title, str)
        assert isinstance(mock_movie.year, int)
        assert isinstance(mock_movie.genres, str)  # JSON строка
        assert isinstance(mock_movie.embedding, str)  # JSON строка
        
        assert isinstance(mock_prediction.input_text, str)
        assert isinstance(mock_prediction.cost, float)
        assert isinstance(mock_prediction.embedding, str)  # JSON строка
    
    def test_movie_data_integration(self, mock_movie_data, mock_movie):
        """Тест интеграции данных фильма"""
        # Проверяем что данные фильма корректно интегрированы
        assert mock_movie.title == mock_movie_data["title"]
        assert mock_movie.description == mock_movie_data["description"]
        assert mock_movie.year == mock_movie_data["year"]
        
        # Проверяем что ARRAY и Vector поля корректно обрабатываются
        import json
        genres = json.loads(mock_movie.genres)
        embedding = json.loads(mock_movie.embedding)
        
        assert genres == mock_movie_data["genres"]
        assert len(embedding) == len(mock_movie_data["embedding"])
    
    def test_transaction_lifecycle(self, mock_user, mock_transaction, session):
        """Тест полного жизненного цикла транзакции"""
        # Проверяем создание транзакции
        assert mock_transaction.id is not None
        assert mock_transaction.user_id == mock_user.id
        assert mock_transaction.wallet_id == mock_user.wallet.id
        
        # Проверяем что транзакция сохранилась в базе
        from tests.conftest import TestTransaction
        saved_transaction = session.get(TestTransaction, mock_transaction.id)
        assert saved_transaction is not None
        assert saved_transaction.amount == 100.0
        assert saved_transaction.type == "DEPOSIT"
    
    def test_transaction_data_integrity(self, mock_transaction):
        """Тест целостности данных транзакции"""
        # Проверяем все поля транзакции
        assert mock_transaction.id > 0
        assert mock_transaction.user_id > 0
        assert mock_transaction.wallet_id > 0
        assert mock_transaction.amount == 100.0
        assert mock_transaction.type == "DEPOSIT"
        assert mock_transaction.description == "Test deposit transaction"
        assert mock_transaction.timestamp is not None
        
        # Проверяем типы данных
        assert isinstance(mock_transaction.id, int)
        assert isinstance(mock_transaction.user_id, int)
        assert isinstance(mock_transaction.wallet_id, int)
        assert isinstance(mock_transaction.amount, float)
        assert isinstance(mock_transaction.type, str)
        assert isinstance(mock_transaction.description, str)
        from datetime import datetime
        assert isinstance(mock_transaction.timestamp, datetime)
    
    def test_transaction_user_wallet_consistency(self, mock_user, mock_transaction):
        """Тест консистентности связей транзакции с пользователем и кошельком"""
        # Проверяем что ID пользователя и кошелька в транзакции соответствуют реальным объектам
        assert mock_transaction.user_id == mock_user.id
        assert mock_transaction.wallet_id == mock_user.wallet.id
        
        # Проверяем что кошелек действительно принадлежит пользователю
        assert mock_user.wallet.user_id == mock_user.id
        
        # Проверяем что транзакция ссылается на существующий кошелек
        assert mock_transaction.wallet_id == mock_user.wallet.id