from typing import Dict
from fastapi import APIRouter, HTTPException
from services.rm.rm import send_task

ml_route = APIRouter()

@ml_route.post(
    "/send_task", 
    response_model=Dict[str, str],
    summary="ML endpoint",
    description="Send ml request"
)
async def index(message:str) -> str:
    """
    Root endpoint returning welcome message.

    Returns:
        Dict[str, str]: Welcome message
    """
    try:
        send_task(message)
        return {"message": f"Task sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
