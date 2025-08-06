from __future__ import annotations
from database.config import get_settings
from services.crud.movie_service import MovieService
from models.prediction import PredictionMovieLink
from models.user import User
from models.wallet import Wallet
from models.movie import Movie
from models.prediction import Prediction
import time
import logging
from sqlalchemy import create_engine, text
from database.config import get_settings # Импортируем настройки

# Настройка логгирования (по желанию, но полезно)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(max_retries=30, retry_interval=1):
    """Ожидает, пока база данных не будет готова принимать соединения."""
    settings = get_settings()
    db_url = settings.DATABASE_URL_psycopg # Используем URL из настроек
    logger.info(f"Попытка подключения к БД по адресу: {settings.POSTGRES_HOST}")

    retries = 0
    while retries < max_retries:
        try:
            # Пытаемся создать движок и подключиться
            engine = create_engine(db_url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1")) # Простой запрос для проверки
            logger.info("Успешное подключение к базе данных.")
            return True # Успешно подключились
        except Exception as e:
            logger.warning(f"База данных недоступна (попытка {retries + 1}/{max_retries}): {e}")
            retries += 1
            if retries < max_retries:
                time.sleep(retry_interval)
    logger.error("Не удалось подключиться к базе данных после нескольких попыток.")
    return False # Не удалось подключиться

if __name__ == "__main__":
    # Ждем готовности базы данных
    if not wait_for_db():
         # Вы можете выбрать, завершать ли работу или продолжать
         # raise RuntimeError("Невозможно продолжить без подключения к БД")
         pass # Или просто продолжаем, надеясь, что следующие операции сами обработают ошибку
    # from services.crud.movie_service import MovieService
    # # Инициализируем сервис
    # MovieService().initialize_demo_database()
    settings = get_settings()
    print(settings)