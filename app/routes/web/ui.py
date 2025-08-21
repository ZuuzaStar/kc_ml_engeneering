from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

web_ui = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="templates")

@web_ui.get("/web", response_class=HTMLResponse)
async def web_index(request: Request):
    """Главная страница веб-интерфейса"""
    return templates.TemplateResponse("index.html", {"request": request})

@web_ui.get("/web/prediction-history", response_class=HTMLResponse)
async def web_prediction_history(request: Request):
    """Страница истории предсказаний"""
    return templates.TemplateResponse("prediction_history.html", {"request": request})

@web_ui.get("/web/transaction-history", response_class=HTMLResponse)
async def web_transaction_history(request: Request):
    """Страница истории транзакций"""
    return templates.TemplateResponse("transaction_history.html", {"request": request})