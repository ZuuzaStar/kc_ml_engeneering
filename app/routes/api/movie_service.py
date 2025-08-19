from fastapi import APIRouter, Body, HTTPException, status, Depends
from services.crud import wallet as WalletService
from services.crud import prediction as PredictionService
from database.database import get_session
from models import PredictionOut, MovieOut
from models.movie import Movie
from models.user import User
from services.crud import user as UserService
from typing import List
from services.rm.rm import MLServiceRpcClient
from models.constants import TransactionCost, TransactionType
from database.config import get_settings
from pgvector.sqlalchemy import Vector
from sqlmodel import select
from auth.basic import get_current_user

movie_service_route = APIRouter()

@movie_service_route.get(
    "/prediction/history",
    response_model=List[PredictionOut]
)
async def get_prediction_history(
    user: User, 
    session=Depends(get_session)
    ) -> List[PredictionOut]:
    user = UserService.get_user_by_email(user.email, session)
    return user.predictions

@movie_service_route.post(
    "/prediction/new",
    response_model=List[MovieOut]
)
async def new_prediction(
    user: User, 
    message: str,
    top: int = 10,
    session=Depends(get_session)
) -> List[MovieOut]: 
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
        movies = session.exec(
            select(Movie)
            .order_by(Movie.embedding.cast(Vector).op("<=>")(response["request_embedding"]))
            .limit(top)
        ).all()

        # Сохраняем предикт в базу
        PredictionService.create_prediction(user, message, response["request_embedding"], cost, movies, session)

        return movies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@movie_service_route.get("/prediction/history-auth", response_model=List[PredictionOut])
async def get_prediction_history_auth(
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[PredictionOut]:
    user = UserService.get_user_by_email(user.email, session)
    return user.predictions

@movie_service_route.post("/prediction/new-auth", response_model=List[MovieOut])
async def new_prediction_auth(
    message: str,
    top: int = 10,
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[MovieOut]:
    if top <= 0:
        raise HTTPException(status_code=400, detail="Invalid 'top' value")
    user = UserService.get_user_by_email(user.email, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cost = TransactionCost.ADMIN.value if user.is_admin else TransactionCost.BASIC.value
    try:
        WalletService.make_transaction(user.wallet, -cost, TransactionType.PREDICTION, session)
    except Exception as e:
        raise HTTPException(status_code=402, detail=str(e))
    try:
        ml_service_rpc = MLServiceRpcClient(get_settings())
        response = ml_service_rpc.call(message)
        movies = session.exec(
            select(Movie)
            .order_by(Movie.embedding.cast(Vector).op("<=>")(response["request_embedding"]))
            .limit(top)
        ).all()
        PredictionService.create_prediction(user, message, response["request_embedding"], cost, movies, session)
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))