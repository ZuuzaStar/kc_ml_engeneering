from fastapi import APIRouter, Body, HTTPException, status, Depends
from app.services.crud import wallet as WalletService
from app.services.crud import prediction as PredictionService
from database.database import get_session
from models.prediction import Prediction
from models.movie import Movie
from models.user import User
from services.crud import user as UserService
from typing import List
from services.rm.rm import MLServiceRpcClient
from models.constants import TransactionCost, TransactionType
from database.config import get_settings
from pgvector.sqlalchemy import Vector
from sqlmodel import select

movie_service_route = APIRouter()

@movie_service_route.get(
    "/prediction/history", 
    response_model=List[Prediction]
) 
async def get_prediction_history(
    user: User, 
    session=Depends(get_session)
    ) -> List[Prediction]:
    user = UserService.get_user_by_email(user.email, session)
    predictions = user.predictions
    return predictions

@movie_service_route.post(
    "/prediction/new",
    response_model=List[Movie]
)
async def new_prediction(
    user: User, 
    message: str,
    top: int = 10,
    session=Depends(get_session)
) -> List[Movie]: 
    """
    Эндпоинт, возвращающий рекомендации

    Returns:
        List[Movie]: Список фильмов
    """
    if not session.get(User, user.id):
        raise ValueError("Пользователя с таким id не существует")
    if user.is_admin:
        cost = TransactionCost.ADMIN.value
    else:
        cost = TransactionCost.BASIC.value
    try:
        WalletService.make_transaction(user.wallet, -cost, TransactionType.PREDICTION, session)
    except Exception as e:
        raise e
    try:
        ml_service_rpc = MLServiceRpcClient(get_settings())
        response = ml_service_rpc.call(message)

        # Поиск подходящих фильмов
        movies = session.scalars(
            select(Movie)
            .order_by(Movie.embedding.cast(Vector).op("<=>")(response["request_embedding"]))
            .limit(top)
        ).all()

        # Сохраняем предикт в базу
        PredictionService.create_prediction(user, message, response, cost, movies, session)

        return movies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

