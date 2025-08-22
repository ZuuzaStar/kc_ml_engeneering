from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from loguru import logger
import threading
from routes.bot.raw import bot

from routes.api import user, movie_service
from routes.web.ui import web_ui
from database.database import init_db
from database.config import get_settings

def create_application() -> FastAPI:
    """Создает и настраивает FastAPI приложение"""
    app = FastAPI(
        title="Movie Recommendation Service",
        description="ML-powered movie recommendation service with user management and balance system",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Setup Jinja2 templates
    templates = Jinja2Templates(directory="templates")
    
    # Include API routers
    app.include_router(user.user_route, prefix="/api/users", tags=["Users"])
    app.include_router(movie_service.movie_service_route, prefix="/api/events", tags=["Movies"])
    
    # Include Web UI router
    app.include_router(web_ui, tags=['Web'])
    
    # Security middleware for logging
    @app.middleware("http")
    async def security_logging_middleware(request: Request, call_next):
        """Логирует доступ к защищенным endpoint'ам и попытки аутентификации"""
        # Log the request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Check if this is an authentication endpoint
        if request.url.path in ["/api/users/signin", "/api/users/signup"]:
            logger.info(f"Authentication attempt: {request.method} {request.url.path}")
        
        response = await call_next(request)
        return response
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Добавляет заголовки безопасности к ответам"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
    
    # Attack prevention middleware
    @app.middleware("http")
    async def attack_prevention_middleware(request: Request, call_next):
        """Предотвращает распространенные паттерны атак"""
        # Block suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "x-forwarded-proto"]
        for header in suspicious_headers:
            if header in request.headers:
                logger.warning(f"Suspicious header detected: {header}")
                return HTMLResponse(content="Suspicious request", status_code=400)
        
        # Block overly long paths
        if len(request.url.path) > 200:
            logger.warning(f"Path too long: {len(request.url.path)} characters")
            return HTMLResponse(content="Path too long", status_code=400)
        
        # Block overly long query parameters
        if len(str(request.query_params)) > 1000:
            logger.warning(f"Query parameters too long: {len(str(request.query_params))} characters")
            return HTMLResponse(content="Query parameters too long", status_code=400)
        
        response = await call_next(request)
        return response
    
    # Start Telegram bot in background thread
    def start_bot():
        """Запускает Telegram бота в фоновом потоке"""
        try:
            if bot:  # Check if bot object was initialized (i.e., BOT_TOKEN was set)
                logger.info("Starting Telegram bot...")
                bot.polling(none_stop=True, timeout=60)
            else:
                logger.warning("Telegram bot not available - BOT_TOKEN not set")
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")

    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot thread started")
    
    return app

app = create_application()

@app.on_event("startup")
async def startup_event():
    """Инициализирует базу данных при запуске приложения."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}