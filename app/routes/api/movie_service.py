from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.prediction import Prediction
from models.movie import Movie
from models.user import User
from services.crud import user as UserService
from services.crud.movie_service import MovieService
from typing import List

movie_service_route = APIRouter()

@movie_service_route.get("/prediction_history", response_model=List[Prediction]) 
async def get_prediction_history(
    data: User, 
    session=Depends(get_session)
    ) -> List[Prediction]:
    user = UserService.get_user_by_email(data.email, session)
    predictions = user.predictions
    return predictions

@movie_service_route.post("/new_prediction")
async def new_prediction(data: User, input_text: str, session=Depends(get_session)) -> List[Movie]: 
    user = UserService.get_user_by_email(data.email, session)
    prediction = MovieService().recommend_movies(user.id, input_text)
    return prediction
