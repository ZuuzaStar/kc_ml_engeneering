from app.bot import bot
import logging
from services.crud import user as UserService
from services.crud.movie_service import MovieService
from database.database import get_session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start."""
    logger.info(f"Пользователь {message.from_user.id} запустил бота.")
    welcome_text = (
        "Добро пожаловать в Movie Recommendation Bot! 🎬\n"
        "Я могу помочь вам найти фильмы по вашему вкусу.\n\n"
        "Доступные команды:\n"
        "/predict - Получить рекомендации фильмов\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['predict'])
def predict_start(message):
    """
    Предсказание.
    Не уверен тут насчет корректности метода.
    Нужна будет корректировка.
    """
    with get_session() as session:
        user = UserService.get_user_by_id(message.from_user.id, session)
        prediction = MovieService.recommend_movies(user.id, message.text)
        return prediction
    