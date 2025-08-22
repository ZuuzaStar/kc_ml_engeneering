from typing import List
from models.movie import Movie
from models.prediction import Prediction
from models.user import User
from sqlmodel import Session, select
from services.crud import user as UserService
from loguru import logger
from pgvector.sqlalchemy import Vector


def create_prediction(
    user: User,
    input_text: str,
    embedding: list,
    cost: float,
    movies: List[Movie],
    session: Session
) -> Prediction:
    """
    Создание экземпляра предсказания модели.
    
    Args:
        user: экземпляр пользователя
        input_text: входящий запрос
        embedding: эмбеддинг входящего запроса
        cost: стоимость предсказания
        movies: список рекомендованных фильмов
        session: сессия базы данных
    
    Returns:
        Prediction: новое предсказание
    """
    prediction = Prediction(
        user_id=user.id,
        input_text=input_text,
        embedding=embedding,
        cost=cost,
        user=user,
        movies=movies
    )
    
    session.add(prediction)
    session.commit()
    session.refresh(prediction)

    return prediction

def get_all_predictions(
    session: Session
) -> List[Prediction]:
    """
    Запрашивает все предсказания из базы.
    
    Args:
        session: сессия базы данных
    
    Returns:
        List[Wallet]: Список предсказаний
    """
    try:
        statement = select(Prediction)
        predictions = session.exec(statement).all()
        return predictions
    except Exception as e:
        logger.error(f"Ошибка при получении всех предсказаний: {e}")
        raise

def get_prediction_by_id(
    id: int,
    session: Session
) -> bool:
    """Получает предсказание по ID"""
    try:
        prediction = session.get(Prediction, id)
        return prediction
    except Exception as e:
        logger.error(f"Ошибка при получении предсказания по ID {id}: {e}")
        raise

def get_prediction_by_user_id(
    id: int,
    session: Session
) -> List[Prediction]:
    """
    Получить все предсказания по ID пользователя.
    
    Args:
        user_id: ID пользователя
        session: сессия базы данных
    
    Returns:
        Optional[Wallet]: Найденный кошелек или None
    """
    user = UserService.get_user_by_id(id, session)
    try:
        statement = select(Prediction).where(Prediction.user_id == user.id)
        predictions = session.exec(statement).all()
        return predictions
    except Exception as e:
        logger.error(f"Ошибка при получении истории предсказаний по ID пользователя {id}: {e}")
        raise
