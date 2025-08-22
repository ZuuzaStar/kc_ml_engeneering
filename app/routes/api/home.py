from typing import Dict
from fastapi import APIRouter, HTTPException

home_route = APIRouter()

@home_route.get(
    "/", 
    response_model=Dict[str, str],
    summary="Root endpoint",
    description="Returns a welcome message"
)
async def index() -> str:
    """
    Главный endpoint, возвращающий приветственное сообщение.

    Returns:
        Dict[str, str]: Приветственное сообщение
    """
    try:
        return {"message": "Welcome to Movie Recommender API"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@home_route.get(
    "/health",
    response_model=Dict[str, str],
    summary="Health check endpoint",
    description="Returns service health status"
)
async def health_check() -> Dict[str, str]:
    """
    Endpoint проверки состояния здоровья сервиса для мониторинга.

    Returns:
        Dict[str, str]: Сообщение о состоянии здоровья
    
    Raises:
        HTTPException: Если сервис нездоров
    """
    try:
        # Add actual health checks here
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail="Service unavailable"
        )

