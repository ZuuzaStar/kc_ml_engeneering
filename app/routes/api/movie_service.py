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
from sqlalchemy import text
from loguru import logger


movie_service_route = APIRouter()

@movie_service_route.get(
    "/prediction/history",
    response_model=List[PredictionOut]
)
async def get_prediction_history(
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[PredictionOut]:
    """
    Get prediction history for authenticated user.

    Args:
        user: Current authenticated user
        session: Database session

    Returns:
        List[PredictionOut]: List of user predictions
    """
    try:
        return user.predictions
    except Exception as e:
        logger.error(f"Error getting prediction history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting prediction history"
        )

@movie_service_route.post(
    "/prediction/new",
    response_model=List[MovieOut]
)
async def new_prediction(
    message: str,
    top: int = 10,
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[MovieOut]:
    """
    Get movie recommendations for authenticated user.

    Args:
        message: User request text
        top: Number of recommendations to return
        user: Current authenticated user
        session: Database session

    Returns:
        List[MovieOut]: List of recommended movies
    """
    if top <= 0:
        raise HTTPException(status_code=400, detail="Invalid 'top' value")
    
    try:
        cost = TransactionCost.ADMIN.value if user.is_admin else TransactionCost.BASIC.value
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