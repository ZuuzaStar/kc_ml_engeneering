from __future__ import annotations
from database.config import get_settings
from services.crud.movie import (
    update_movie_database, 
    get_all_movies
)
import time
import logging
from sqlalchemy import create_engine, text
from database.database import engine
from sqlmodel import Session
from sentence_transformers import SentenceTransformer
from models.constants import ModelTypes


# Настройка логгирования (по желанию, но полезно)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(max_retries=30, retry_interval=1):
    """Ожидает, пока база данных не будет готова принимать соединения."""
    settings = get_settings()
    db_url = settings.DATABASE_URL_psycopg
    logger.info(f"Попытка подключения к БД по адресу: {settings.POSTGRES_HOST}")

    retries = 0
    while retries < max_retries:
        try:
            # Пытаемся создать движок и подключиться
            temp_engine = create_engine(db_url)
            with temp_engine.connect() as connection:
                connection.execute(text("SELECT 1"))  # Простой запрос для проверки
            logger.info("Успешное подключение к базе данных.")
            return True  # Успешно подключились
        except Exception as e:
            logger.warning(f"База данных недоступна (попытка {retries + 1}/{max_retries}): {e}")
            retries += 1
            if retries < max_retries:
                time.sleep(retry_interval)
    logger.error("Не удалось подключиться к базе данных после нескольких попыток.")
    return False  # Не удалось подключиться

if __name__ == "__main__":
    # Ждем готовности базы данных
    if not wait_for_db():
        logger.error("Не удалось подключиться к БД")
        exit(1)
    
    # Импортируем все модели для корректного создания таблиц
    from sqlmodel import SQLModel
    from models.movie import Movie
    from models.user import User
    from models.prediction import Prediction
    from models.wallet import Wallet
    from models.transaction import Transaction
    from models.prediction_movie_link import PredictionMovieLink
    
    # Настраиваем реестр для корректной работы связей
    from sqlmodel import SQLModel
    from sqlalchemy.orm import configure_mappers
    
    # Явно настраиваем мапперы для корректной работы связей
    configure_mappers()
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Проверяем количество фильмов в базе
        movies_count = len(get_all_movies(session))
        logger.info(f"В базе данных найдено {movies_count} фильмов")
        
        # Если фильмов нет, загружаем из JSON файлов
        if movies_count == 0:
            logger.info("Загружаем фильмы из JSON файлов...")
            model = SentenceTransformer('sentence-transformers/' + ModelTypes.MULTILINGUAL.value)
            update_movie_database(model, session)
            logger.info('База данных с фильмами успешно обновлена')
            
            # Для максимальной точности не создаем ivfflat индекс
            logger.info("Пропускаем создание ivfflat индекса для максимальной точности поиска")
            
            # # Создаем векторный индекс после загрузки фильмов
            # logger.info("Создаем векторный индекс для быстрого поиска...")
            # try:
            #     with engine.connect() as connection:
            #         connection.execute(text("CREATE INDEX IF NOT EXISTS idx_movie_embedding_ivfflat ON movie USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"))
            #         connection.commit()
            #     logger.info("Векторный индекс успешно создан")
            # except Exception as e:
            #     logger.warning(f"Не удалось создать векторный индекс: {e}")
        else:
            logger.info('База данных уже содержит фильмы')
            
            # Для максимальной точности не создаем ivfflat индекс
            logger.info("Пропускаем создание ivfflat индекса для максимальной точности поиска")
            
            # # Проверяем существование индекса
            # try:
            #     with engine.connect() as connection:
            #         result = connection.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'movie' AND indexname = 'idx_movie_embedding_ivfflat'"))
            #         if not result.fetchone():
            #             logger.info("Создаем векторный индекс для существующих фильмов...")
            #             connection.execute(text("CREATE INDEX IF NOT EXISTS idx_movie_embedding_ivfflat ON movie USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"))
            #             connection.commit()
            #             logger.info("Векторный индекс успешно создан")
            #         else:
            #             logger.info("Векторный индекс уже существует")
            # except Exception as e:
            #     logger.warning(f"Не удалось создать векторный индекс: {e}")
