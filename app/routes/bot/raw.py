from app.bot import bot, user_states
import logging
from services.crud import user as UserService
from services.crud.movie_service import MovieService
from database.database import get_session
from models.user import User
from sqlmodel import Session

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
        "/history - История ваших рекомендаций\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['predict'])
def predict_start(message):
    """Начало процесса получения рекомендаций"""
    chat_id = message.chat.id
    user_states[chat_id] = 'waiting_for_description'
    bot.reply_to(message, "Пожалуйста, опишите, какие фильмы вы хотите найти (минимум 10 символов):")

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id] == 'waiting_for_description')
def handle_description(message):
    """Обработка описания для рекомендаций"""
    chat_id = message.chat.id
    input_text = message.text
    
    if len(input_text) < 10:
        bot.reply_to(message, "Пожалуйста, введите описание длиной не менее 10 символов.")
        return
    
    try:
        # Здесь должна быть логика получения пользователя из Telegram ID
        # Для демонстрации создадим или найдем пользователя
        with next(get_session()) as session:
            # Проверяем, существует ли пользователь с таким Telegram ID
            # В реальной реализации нужно хранить связь Telegram ID <-> User ID
            user = session.exec(User.email == "user@example.com").first()
            if not user:
                bot.reply_to(message, "Ошибка: пользователь не найден.")
                return
            
            # Отправляем задачу на рекомендацию
            try:
                task_id = MovieService().request_recommendation_async(user.id, input_text, session)
                bot.reply_to(message, 
                    f"Ваш запрос на рекомендацию принят!\n"
                    f"ID задачи: {task_id}\n"
                    f"Описание: {input_text}\n\n"
                    f"Рекомендации будут доступны через несколько секунд. "
                    f"Вы можете проверить статус с помощью команды /status_{task_id[-8:]}")
            except Exception as e:
                bot.reply_to(message, f"Ошибка при отправке запроса: {str(e)}")
                
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при обработке вашего запроса.")
    
    # Очищаем состояние
    if chat_id in user_states:
        del user_states[chat_id]

@bot.message_handler(commands=['history'])
def show_history(message):
    """Показ истории рекомендаций"""
    try:
        with next(get_session()) as session:
            user = session.exec(User.email == "user@example.com").first()
            if not user:
                bot.reply_to(message, "Ошибка: пользователь не найден.")
                return
            
            predictions = user.predictions
            if not predictions:
                bot.reply_to(message, "У вас пока нет истории рекомендаций.")
                return
            
            response = "Ваша история рекомендаций:\n\n"
            for i, pred in enumerate(predictions[-5:], 1):  # Показываем последние 5
                response += f"{i}. {pred.input_text[:50]}...\n"
                response += f"   Стоимость: {pred.cost}\n"
                response += f"   Дата: {pred.created_at.strftime('%Y-%m-%d %H:%M') if pred.created_at else 'N/A'}\n\n"
            
            bot.reply_to(message, response)
            
    except Exception as e:
        logger.error(f"Ошибка получения истории: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при получении истории.")