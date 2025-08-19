from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from routes.api.home import home_route
from routes.api.user import user_route
from routes.api.movie_service import movie_service_route
from database.database import init_db
from database.config import get_settings
import uvicorn
import logging
from routes.web.ui import web_ui
from sqlmodel import Session
from database.database import engine
import time

logger = logging.getLogger(__name__)
settings = get_settings()

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Register routes
    app.include_router(home_route, tags=['Home'])
    app.include_router(user_route, prefix='/api/users', tags=['Users'])
    app.include_router(movie_service_route, prefix='/api/events', tags=['MovieService'])
    app.include_router(web_ui, tags=['Web'])

    return app

app = create_application()

# Security middleware
@app.middleware("http")
async def security_logging_middleware(request: Request, call_next):
    """
    Middleware for logging security-related information.
    """
    start_time = time.time()
    
    # Log all requests to protected endpoints
    if any(protected_path in request.url.path for protected_path in [
        "/api/users/balance",
        "/api/users/balance/adjust", 
        "/api/users/transaction/history",
        "/api/events/prediction/history",
        "/api/events/prediction/new"
    ]):
        logger.info(f"Protected endpoint access: {request.method} {request.url.path} from {request.client.host}")
    
    # Log authentication attempts
    if request.url.path in ["/api/users/signin", "/api/users/signup"]:
        logger.info(f"Authentication attempt: {request.method} {request.url.path} from {request.client.host}")
    
    response = await call_next(request)
    
    # Log response time for performance monitoring
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "app", "web-proxy"]
)

# Security middleware for attack prevention
@app.middleware("http")
async def attack_prevention_middleware(request: Request, call_next):
    """
    Middleware for preventing common attacks.
    """
    # Block requests with suspicious headers
    suspicious_headers = [
        'x-forwarded-for', 'x-real-ip', 'x-forwarded-proto',
        'x-forwarded-host', 'x-forwarded-server'
    ]
    
    for header in suspicious_headers:
        if header in request.headers:
            logger.warning(f"Suspicious header detected: {header} from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request headers"
            )
    
    # Block requests with extremely long paths
    if len(request.url.path) > 200:
        logger.warning(f"Path too long from {request.client.host}: {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path too long"
        )
    
    # Block requests with suspicious query parameters
    if any(len(str(v)) > 100 for v in request.query_params.values()):
        logger.warning(f"Query parameter too long from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter too long"
        )
    
    response = await call_next(request)
    return response

@app.on_event("startup") 
def on_startup():
    try:
        logger.info("Initializing database...")
        init_db()
        # Seed movies if empty
        with Session(engine) as session:
            try:
                from services.crud.movie import get_all_movies, update_movie_database
                from sentence_transformers import SentenceTransformer
                from models.constants import ModelTypes
                if len(get_all_movies(session)) == 0:
                    logger.info("No movies found. Seeding demo/movie dataset...")
                    model = SentenceTransformer('sentence-transformers/' + ModelTypes.MULTILINGUAL.value)
                    update_movie_database(model, session)
                    logger.info("Movie dataset seeded")
            except Exception as seed_err:
                logger.warning(f"Movie seeding skipped/failed: {seed_err}")
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Application shutting down...")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="info"
    )