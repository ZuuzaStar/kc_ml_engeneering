from __future__ import annotations
from database.config import get_settings
from services.crud import user as UserServices
from services.crud import wallet as WalletServices
from models.user import User
from models.wallet import Wallet
from services.crud.movie_service import MovieService
from models.prediction import PredictionMovieLink
from models.movie import Movie
from models.prediction import Prediction
import time
import logging
from sqlalchemy import create_engine, text
from database.database import engine
from sqlmodel import Session


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
        logger.error("Не удалось подключиться к БД")
        exit(1)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # MovieService().initialize_demo_database(session)
        settings = get_settings()
        print(settings)
        new_wallet = Movie()
        # new_wallet = WalletServices.create_wallet(new_wallet, session)
        # new_user = User(
        #     email='example@mail.ru',
        #     password_hash=UserServices.hash_password('example123'),
        #     wallet=new_wallet
        # )
        # UserServices.create_user(
        #      new_user, session
        # )