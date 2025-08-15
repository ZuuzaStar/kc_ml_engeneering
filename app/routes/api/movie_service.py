from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.prediction import Prediction
from models.movie import Movie
from models.user import User
from services.crud import user as UserService
from typing import List
from services.rm.rm import send_task

movie_service_route = APIRouter()

@movie_service_route.get(
    "/prediction/history", 
    response_model=List[Prediction]
) 
async def get_prediction_history(
    data: User, 
    session=Depends(get_session)
    ) -> List[Prediction]:
    user = UserService.get_user_by_email(data.email, session)
    predictions = user.predictions
    return predictions

@movie_service_route.post(
    "/prediction/new",
    response_model=List[Movie]
)
async def new_prediction(message: str, session=Depends(get_session)) -> List[Movie]: 
    """
    Эндпоинт, возвращающий рекомендации

    Returns:
        List[Movie]: Список фильмов
    """
    try:
        send_task(message)
        return {"message": f"Task sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
