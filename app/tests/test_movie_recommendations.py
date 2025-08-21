import pytest
from fastapi.testclient import TestClient
import json


class TestMovieRecommendations:
    """Тесты для рекомендаций фильмов"""
    
    def test_health_endpoint_works(self, client, session):
        """Тест работы тестового приложения"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_movie_model_creation(self, mock_movie):
        """Тест создания модели фильма"""
        assert mock_movie.title == "Test Movie"
        assert mock_movie.year == 2023
        
        # Тестируем ARRAY поле (сохраненное как JSON)
        genres = json.loads(mock_movie.genres)
        assert isinstance(genres, list)
        assert "action" in genres
        assert "drama" in genres
        
        # Тестируем Vector поле (сохраненное как JSON)
        embedding = json.loads(mock_movie.embedding)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_prediction_model_creation(self, mock_prediction):
        """Тест создания модели предсказания"""
        assert mock_prediction.input_text == "I want to watch an action movie"
        assert mock_prediction.cost == 1.0
        
        # Тестируем Vector поле (сохраненное как JSON)
        embedding = json.loads(mock_prediction.embedding)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_movie_array_field_emulation(self, mock_movie):
        """Тест эмуляции поля ARRAY в модели фильма"""
        # Проверяем что жанры сохраняются как JSON строка и восстанавливаются как список
        genres = json.loads(mock_movie.genres)
        assert isinstance(genres, list)
        assert len(genres) == 2
        assert "action" in genres
        assert "drama" in genres
        
        # Проверяем что можно добавлять новые жанры
        genres.append("comedy")
        mock_movie.genres = json.dumps(genres)
        updated_genres = json.loads(mock_movie.genres)
        assert "comedy" in updated_genres
    
    def test_movie_vector_field_emulation(self, mock_movie):
        """Тест эмуляции поля Vector в модели фильма"""
        # Проверяем что embedding сохраняется как JSON строка
        embedding = json.loads(mock_movie.embedding)
        assert mock_movie.embedding is not None
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        
        # Проверяем что можно изменять embedding
        new_embedding = [0.5] * 384
        mock_movie.embedding = json.dumps(new_embedding)
        updated_embedding = json.loads(mock_movie.embedding)
        assert updated_embedding == new_embedding
    
    def test_prediction_vector_field_emulation(self, mock_prediction):
        """Тест эмуляции поля Vector в модели предсказания"""
        # Проверяем что embedding сохраняется как JSON строка
        embedding = json.loads(mock_prediction.embedding)
        assert mock_prediction.embedding is not None
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        
        # Проверяем что можно изменять embedding
        new_embedding = [0.3] * 384
        mock_prediction.embedding = json.dumps(new_embedding)
        updated_embedding = json.loads(mock_prediction.embedding)
        assert updated_embedding == new_embedding
    
    def test_json_serialization_deserialization(self, mock_movie, mock_prediction):
        """Тест сериализации и десериализации JSON для ARRAY и Vector полей"""
        # Тестируем фильм
        movie_genres = json.loads(mock_movie.genres)
        movie_embedding = json.loads(mock_movie.embedding)
        
        # Проверяем что данные корректно восстанавливаются
        assert movie_genres == ["action", "drama"]
        assert len(movie_embedding) == 384
        
        # Тестируем предсказание
        pred_embedding = json.loads(mock_prediction.embedding)
        assert len(pred_embedding) == 384
        assert all(x == 0.1 for x in pred_embedding)
    
    def test_data_consistency(self, mock_movie, mock_prediction):
        """Тест консистентности данных между ARRAY и Vector полями"""
        # Проверяем что все поля корректно заполнены
        assert mock_movie.title is not None
        assert mock_movie.description is not None
        assert mock_movie.year > 0
        assert mock_movie.genres is not None
        assert mock_movie.embedding is not None
        
        # Проверяем что JSON валиден
        try:
            json.loads(mock_movie.genres)
            json.loads(mock_movie.embedding)
            json.loads(mock_prediction.embedding)
        except json.JSONDecodeError:
            pytest.fail("JSON поля должны быть валидными")
    
    def test_movie_data_fixture(self, mock_movie_data):
        """Тест фикстуры mock_movie_data"""
        # Проверяем структуру данных фильма
        assert "title" in mock_movie_data
        assert "description" in mock_movie_data
        assert "year" in mock_movie_data
        assert "genres" in mock_movie_data
        assert "embedding" in mock_movie_data
        
        # Проверяем типы данных
        assert isinstance(mock_movie_data["title"], str)
        assert isinstance(mock_movie_data["description"], str)
        assert isinstance(mock_movie_data["year"], int)
        assert isinstance(mock_movie_data["genres"], list)
        assert isinstance(mock_movie_data["embedding"], list)
        
        # Проверяем конкретные значения
        assert mock_movie_data["title"] == "Test Movie"
        assert mock_movie_data["year"] == 2023
        assert mock_movie_data["genres"] == ["action", "drama"]
        assert len(mock_movie_data["embedding"]) == 384
        assert all(x == 0.1 for x in mock_movie_data["embedding"])
    
    def test_movie_data_to_model_mapping(self, mock_movie_data, mock_movie):
        """Тест соответствия данных фикстуры и модели"""
        # Проверяем что данные из фикстуры корректно маппятся в модель
        assert mock_movie.title == mock_movie_data["title"]
        assert mock_movie.description == mock_movie_data["description"]
        assert mock_movie.year == mock_movie_data["year"]
        
        # Проверяем что жанры и embedding корректно сериализуются
        import json
        genres_from_model = json.loads(mock_movie.genres)
        embedding_from_model = json.loads(mock_movie.embedding)
        
        assert genres_from_model == mock_movie_data["genres"]
        assert embedding_from_model == mock_movie_data["embedding"]