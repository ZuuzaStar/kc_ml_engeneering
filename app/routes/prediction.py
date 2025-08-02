from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.prediction import prediction 
from typing import List

prediction_router = APIRouter()
predictions = []

@prediction_router.get("/", response_model=List['prediction']) 
async def retrieve_all_predictions() -> List['prediction']:
    return predictions

@prediction_router.get("/{id}", response_model=prediction) 
async def retrieve_prediction(id: int) -> prediction:
    for prediction in predictions: 
        if prediction.id == id:
            return prediction 
    raise HTTPException(status_code=status. HTTP_404_NOT_FOUND, detail="Prediction with supplied ID does not exist")

@prediction_router.post("/new")
async def create_prediction(body: prediction = Body(...)) -> dict: 
    predictions.append(body)
    return {"message": "Prediction created successfully"}

@prediction_router.delete("/{id}")
async def delete_prediction(id: int) -> dict: 
    for prediction in predictions:
        if prediction.id == id: 
            predictions.remove(prediction)
            return {"message": "Prediction deleted successfully"}
        raise HTTPException(status_code=status. HTTP_404_NOT_FOUND, detail="Prediction with supplied ID does not exist")

@prediction_router.delete("/")
async def delete_all_predictions() -> dict: 
    predictions.clear()
    return {"message": "Predictions deleted successfully"}