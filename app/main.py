from database.config import get_settings
# from database.database import get_session, init_db, get_database_engine
from services.crud.movie_service import MovieService
# from sqlmodel import Session
# # from models.event import Event
# from models.user import User


if __name__ == "__main__":
    MovieService().initialize_database()
    settings = get_settings()
    print(settings)