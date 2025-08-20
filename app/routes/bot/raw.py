import os
import telebot
from telebot import types
import logging
from services.crud import user as UserService
from services.crud import prediction as PredictionService
from database.database import get_session
from models.user import User
from sqlmodel import Session
from services.rm.rm import MLServiceRpcClient
from database.config import get_settings
from pgvector.sqlalchemy import Vector
from sqlmodel import select
from models.movie import Movie
import hashlib
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN не установлен. Telegram бот будет отключен.")
    bot = None
    user_states = {}
else:
    bot = telebot.TeleBot(BOT_TOKEN)
    user_states = {}

# Расширенные состояния для авторизации
AUTH_STATES = {
    'waiting_for_email': 'waiting_for_email',
    'waiting_for_password': 'waiting_for_password',
    'waiting_for_description': 'waiting_for_description'
}

# Кэш авторизованных пользователей (telegram_id -> user_id)
authorized_users = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start."""
    if not bot:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем, авторизован ли пользователь
    if user_id in authorized_users:
        show_main_menu(message)
        return
    
    logger.info(f"Новый пользователь {user_id} запустил бота.")
    
    welcome_text = (
        "🎬 Добро пожаловать в Movie Recommendation Bot!\n\n"
        "Я помогу вам найти фильмы по вашему вкусу.\n\n"
        "Для начала работы необходимо авторизоваться.\n"
        "Выберите действие:"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔐 Войти", callback_data="auth_signin"),
        types.InlineKeyboardButton("📝 Регистрация", callback_data="auth_signup")
    )
    
    bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('auth_'))
def handle_auth_callback(call):
    """Обработка callback'ов для авторизации"""
    if not bot:
        return
    
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if call.data == "auth_signin":
        start_signin(chat_id, user_id)
    elif call.data == "auth_signup":
        start_signup(chat_id, user_id)
    elif call.data == "auth_back":
        send_welcome(call.message)

def start_signin(chat_id, user_id):
    """Начало процесса входа"""
    user_states[chat_id] = AUTH_STATES['waiting_for_email']
    user_states[f"{chat_id}_auth_type"] = "signin"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="auth_back"))
    
    bot.send_message(
        chat_id,
        "🔐 Вход в систему\n\n"
        "Пожалуйста, введите ваш email:",
        reply_markup=markup
    )

def start_signup(chat_id, user_id):
    """Начало процесса регистрации"""
    user_states[chat_id] = AUTH_STATES['waiting_for_email']
    user_states[f"{chat_id}_auth_type"] = "signup"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="auth_back"))
    
    bot.send_message(
        chat_id,
        "📝 Регистрация\n\n"
        "Пожалуйста, введите email для регистрации:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: 
    message.chat.id in user_states and 
    user_states[message.chat.id] == AUTH_STATES['waiting_for_email'])
def handle_email_input(message):
    """Обработка ввода email"""
    if not bot:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    email = message.text.strip()
    
    # Простая валидация email
    if '@' not in email or '.' not in email:
        bot.reply_to(message, "❌ Неверный формат email. Попробуйте еще раз:")
        return
    
    # Сохраняем email и переходим к паролю
    user_states[f"{chat_id}_email"] = email
    user_states[chat_id] = AUTH_STATES['waiting_for_password']
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="auth_back"))
    
    auth_type = user_states.get(f"{chat_id}_auth_type", "signin")
    action_text = "регистрации" if auth_type == "signup" else "входа"
    
    bot.reply_to(
        message,
        f"✅ Email сохранен: {email}\n\n"
        f"Теперь введите пароль для {action_text}:\n"
        f"Пароль должен содержать минимум 8 символов, "
        f"включая верхний и нижний регистр, а также цифры.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: 
    message.chat.id in user_states and 
    user_states[message.chat.id] == AUTH_STATES['waiting_for_password'])
def handle_password_input(message):
    """Обработка ввода пароля"""
    if not bot:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    password = message.text.strip()
    email = user_states.get(f"{chat_id}_email", "")
    auth_type = user_states.get(f"{chat_id}_auth_type", "signin")
    
    # Валидация пароля
    if len(password) < 8:
        bot.reply_to(message, "❌ Пароль слишком короткий. Минимум 8 символов.")
        return
    
    if not any(c.isupper() for c in password):
        bot.reply_to(message, "❌ Пароль должен содержать хотя бы одну заглавную букву.")
        return
    
    if not any(c.islower() for c in password):
        bot.reply_to(message, "❌ Пароль должен содержать хотя бы одну строчную букву.")
        return
    
    if not any(c.isdigit() for c in password):
        bot.reply_to(message, "❌ Пароль должен содержать хотя бы одну цифру.")
        return
    
    try:
        with next(get_session()) as session:
            if auth_type == "signup":
                # Регистрация
                result = handle_signup(session, email, password, user_id)
            else:
                # Вход
                result = handle_signin(session, email, password, user_id)
            
            if result['success']:
                # Очищаем состояния
                cleanup_auth_states(chat_id)
                show_main_menu(message)
            else:
                bot.reply_to(message, f"❌ {result['message']}")
                
    except Exception as e:
        logger.error(f"Ошибка авторизации: {str(e)}")
        bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")
        cleanup_auth_states(chat_id)

def handle_signup(session, email, password, telegram_id):
    """Обработка регистрации"""
    try:
        # Проверяем, существует ли пользователь
        existing_user = session.exec(select(User).where(User.email == email)).first()
        if existing_user:
            return {'success': False, 'message': 'Пользователь с таким email уже существует.'}
        
        # Создаем пользователя
        user = UserService.create_user(session, email, password, is_admin=False)
        if user:
            # Сохраняем связь telegram_id -> user_id
            authorized_users[telegram_id] = user.id
            logger.info(f"Пользователь {telegram_id} добавлен в authorized_users: {user.id}")
            logger.info(f"Текущий authorized_users: {authorized_users}")
            return {'success': True, 'message': 'Регистрация успешна!'}
        else:
            return {'success': False, 'message': 'Ошибка создания пользователя.'}
            
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        return {'success': False, 'message': 'Ошибка регистрации.'}

def handle_signin(session, email, password, telegram_id):
    """Обработка входа"""
    try:
        # Ищем пользователя
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            return {'success': False, 'message': 'Пользователь не найден.'}
        
        # Проверяем пароль
        if not UserService.verify_password(password, user.password_hash):
            return {'success': False, 'message': 'Неверный пароль.'}
        
        # Сохраняем связь telegram_id -> user_id
        authorized_users[telegram_id] = user.id
        logger.info(f"Пользователь {telegram_id} добавлен в authorized_users: {user.id}")
        logger.info(f"Текущий authorized_users: {authorized_users}")
        return {'success': True, 'message': 'Вход выполнен успешно!'}
        
    except Exception as e:
        logger.error(f"Ошибка входа: {str(e)}")
        return {'success': False, 'message': 'Ошибка входа.'}

def cleanup_auth_states(chat_id):
    """Очистка состояний авторизации"""
    keys_to_remove = [
        chat_id,
        f"{chat_id}_auth_type",
        f"{chat_id}_email"
    ]
    for key in keys_to_remove:
        if key in user_states:
            del user_states[key]

def show_main_menu(message):
    """Показ главного меню после авторизации"""
    if not bot:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"show_main_menu вызвана для пользователя {user_id}")
    logger.info(f"authorized_users: {authorized_users}")
    logger.info(f"user_id в authorized_users: {user_id in authorized_users}")
    
    if user_id not in authorized_users:
        logger.warning(f"Пользователь {user_id} не авторизован, перенаправляем на /start")
        send_welcome(message)
        return
    
    try:
        with next(get_session()) as session:
            user = session.get(User, authorized_users[user_id])
            if not user:
                logger.error(f"Пользователь {user_id} не найден в БД, удаляем из authorized_users")
                del authorized_users[user_id]
                send_welcome(message)
                return
            
            balance = user.wallet.balance
            logger.info(f"Показываем главное меню для пользователя {user.email} с балансом {balance}")
            
            menu_text = (
                f"🎬 **Главное меню**\n\n"
                f"👤 Пользователь: {user.email}\n"
                f"💳 Баланс: {balance} кредитов\n\n"
                f"Выберите действие:"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.row(
                types.InlineKeyboardButton("🎯 Получить рекомендации", callback_data="menu_predict"),
                types.InlineKeyboardButton("📚 История", callback_data="menu_history")
            )
            markup.row(
                types.InlineKeyboardButton("💳 Баланс", callback_data="menu_balance"),
                types.InlineKeyboardButton("🔧 Настройки", callback_data="menu_settings")
            )
            markup.row(types.InlineKeyboardButton("🚪 Выйти", callback_data="menu_logout"))
            
            bot.send_message(chat_id, menu_text, reply_markup=markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Ошибка показа главного меню: {str(e)}")
        bot.reply_to(message, "❌ Ошибка загрузки меню.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def handle_menu_callback(call):
    """Обработка callback'ов главного меню"""
    if not bot:
        return
    
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if call.data == "menu_predict":
        start_prediction(chat_id, user_id)
    elif call.data == "menu_history":
        show_history(call.message)
    elif call.data == "menu_balance":
        show_balance_for_callback(call.message)
    elif call.data == "menu_settings":
        show_settings(chat_id, user_id)
    elif call.data == "menu_logout":
        handle_logout(call.message)

def start_prediction(chat_id, user_id):
    """Начало процесса получения рекомендаций"""
    if not bot:
        return
    
    if user_id not in authorized_users:
        bot.send_message(chat_id, "❌ Необходимо авторизоваться.")
        return
    
    user_states[chat_id] = AUTH_STATES['waiting_for_description']
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_back"))
    
    bot.send_message(
        chat_id,
        "🎯 Получение рекомендаций\n\n"
        "Пожалуйста, опишите, какие фильмы вы хотите найти "
        "(минимум 10 символов):",
        reply_markup=markup
    )

def handle_logout(message):
    """Выход из системы"""
    if not bot:
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Удаляем из авторизованных
    if user_id in authorized_users:
        del authorized_users[user_id]
    
    # Очищаем состояния
    cleanup_auth_states(chat_id)
    
    bot.reply_to(message, "🚪 Вы вышли из системы.")
    send_welcome(message)

@bot.message_handler(func=lambda message: 
    message.chat.id in user_states and 
    user_states[message.chat.id] == AUTH_STATES['waiting_for_description'])
def handle_description(message):
    """Обработка описания для рекомендаций"""
    if not bot:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    input_text = message.text
    
    if user_id not in authorized_users:
        bot.reply_to(message, "❌ Необходимо авторизоваться.")
        return
    
    if len(input_text) < 10:
        bot.reply_to(message, "❌ Описание должно содержать минимум 10 символов.")
        return
    
    try:
        with next(get_session()) as session:
            user = session.get(User, authorized_users[user_id])
            if not user:
                del authorized_users[user_id]
                bot.reply_to(message, "❌ Пользователь не найден. Авторизуйтесь заново.")
                return
            
            # Проверяем баланс
            if user.wallet.balance < 10:
                bot.reply_to(
                    message, 
                    f"❌ Недостаточно средств. Ваш баланс: {user.wallet.balance}. "
                    f"Пополните баланс через веб-интерфейс."
                )
                return
            
            bot.reply_to(message, "⏳ Обрабатываю ваш запрос...")
            
            try:
                # Получаем эмбеддинг через ML сервис
                ml_service_rpc = MLServiceRpcClient(get_settings())
                response = ml_service_rpc.call(input_text)
                
                # Ищем похожие фильмы
                movies = session.exec(
                    select(Movie)
                    .order_by(Movie.embedding.cast(Vector).op("<=>")(response["request_embedding"]))
                    .limit(10)  # Увеличиваем с 5 до 10
                ).all()
                
                if not movies:
                    bot.reply_to(message, "❌ К сожалению, не удалось найти подходящие фильмы.")
                    return
                
                # Создаем предсказание
                cost = 10.0
                PredictionService.create_prediction(user, input_text, response["request_embedding"], cost, movies, session)
                
                # Формируем ответ - упрощенный формат
                response_text = f"🎬 Найдено {len(movies)} фильмов по запросу: '{input_text}'\n\n"
                for i, movie in enumerate(movies, 1):
                    response_text += f"{i}. **{movie.title}** ({movie.year})\n"
                    response_text += f"   Жанры: {', '.join(movie.genres[:3]) if movie.genres else 'Не указаны'}\n\n"
                
                response_text += f"💰 Стоимость: {cost} кредитов\n"
                response_text += f"💳 Новый баланс: {user.wallet.balance - cost}"
                
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))
                
                bot.reply_to(message, response_text, reply_markup=markup, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Ошибка ML сервиса: {str(e)}")
                bot.reply_to(message, "❌ Ошибка при обработке запроса. Попробуйте позже.")
                
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {str(e)}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке вашего запроса.")
    
    # Очищаем состояние
    if chat_id in user_states:
        del user_states[chat_id]

@bot.message_handler(commands=['history'])
def show_history(message):
    """Показ истории рекомендаций"""
    if not bot:
        return
    
    user_id = message.from_user.id
    
    if user_id not in authorized_users:
        bot.reply_to(message, "❌ Необходимо авторизоваться.")
        return
    
    try:
        with next(get_session()) as session:
            user = session.get(User, authorized_users[user_id])
            if not user:
                del authorized_users[user_id]
                bot.reply_to(message, "❌ Пользователь не найден. Авторизуйтесь заново.")
                return
            
            predictions = user.predictions
            if not predictions:
                bot.reply_to(message, "📚 У вас пока нет истории рекомендаций.")
                return
            
            response = "📚 Ваша история рекомендаций:\n\n"
            for i, pred in enumerate(predictions[-5:], 1):  # Показываем последние 5
                response += f"{i}. {pred.input_text[:50]}...\n"
                response += f"   💰 Стоимость: {pred.cost} кредитов\n"
                response += f"   📅 Дата: {pred.timestamp.strftime('%Y-%m-%d %H:%M') if pred.timestamp else 'N/A'}\n"
                response += f"   🎬 Фильмов: {len(pred.movies) if pred.movies else 0}\n\n"
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))
            
            bot.reply_to(message, response, reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Ошибка получения истории: {str(e)}")
        bot.reply_to(message, "❌ Произошла ошибка при получении истории.")

def show_balance_for_callback(message):
    """Показ баланса пользователя для callback'ов"""
    if not bot:
        return
    
    user_id = message.from_user.id
    
    # Добавляем логирование для отладки
    logger.info(f"Запрос баланса через callback от пользователя {user_id}")
    logger.info(f"authorized_users: {authorized_users}")
    logger.info(f"user_id в authorized_users: {user_id in authorized_users}")
    
    if user_id not in authorized_users:
        bot.reply_to(message, "❌ Необходимо авторизоваться.")
        return
    
    try:
        with next(get_session()) as session:
            user = session.get(User, authorized_users[user_id])
            if not user:
                del authorized_users[user_id]
                bot.reply_to(message, "❌ Пользователь не найден. Авторизуйтесь заново.")
                return
            
            balance = user.wallet.balance
            response = f"💳 Ваш текущий баланс: {balance} кредитов\n\n"
            
            if balance < 10:
                response += "⚠️ Недостаточно средств для получения рекомендаций.\n"
                response += "Пополните баланс через веб-интерфейс: http://localhost/web"
            else:
                response += "✅ Достаточно средств для получения рекомендаций."
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))
            
            bot.reply_to(message, response, reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {str(e)}")
        bot.reply_to(message, "❌ Произошла ошибка при получении баланса.")

@bot.message_handler(commands=['balance'])
def show_balance(message):
    """Показ баланса пользователя"""
    if not bot:
        return
    
    user_id = message.from_user.id
    
    # Добавляем логирование для отладки
    logger.info(f"Запрос баланса от пользователя {user_id}")
    logger.info(f"authorized_users: {authorized_users}")
    logger.info(f"user_id в authorized_users: {user_id in authorized_users}")
    
    if user_id not in authorized_users:
        bot.reply_to(message, "❌ Необходимо авторизоваться.")
        return
    
    try:
        with next(get_session()) as session:
            user = session.get(User, authorized_users[user_id])
            if not user:
                del authorized_users[user_id]
                bot.reply_to(message, "❌ Пользователь не найден. Авторизуйтесь заново.")
                return
            
            balance = user.wallet.balance
            response = f"💳 Ваш текущий баланс: {balance} кредитов\n\n"
            
            if balance < 10:
                response += "⚠️ Недостаточно средств для получения рекомендаций.\n"
                response += "Пополните баланс через веб-интерфейс: http://localhost/web"
            else:
                response += "✅ Достаточно средств для получения рекомендаций."
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))
            
            bot.reply_to(message, response, reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {str(e)}")
        bot.reply_to(message, "❌ Произошла ошибка при получении баланса.")

@bot.message_handler(commands=['help'])
def show_help(message):
    """Показ справки"""
    if not bot:
        return
    
    help_text = (
        "🤖 **Movie Recommendation Bot - Справка**\n\n"
        "**Доступные команды:**\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "**Как использовать:**\n"
        "1. Авторизуйтесь через /start\n"
        "2. Используйте главное меню для навигации\n"
        "3. Получайте персонализированные рекомендации\n\n"
        "**Стоимость:** 10 кредитов за запрос\n"
        "**Веб-интерфейс:** http://localhost/web"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))
    
    bot.reply_to(message, help_text, reply_markup=markup, parse_mode='Markdown')

def show_settings(chat_id, user_id):
    """Показ настроек пользователя"""
    if not bot:
        return
    
    settings_text = (
        "🔧 **Настройки**\n\n"
        "Здесь вы можете управлять своим профилем.\n\n"
        "Функция в разработке..."
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))
    
    bot.send_message(chat_id, settings_text, reply_markup=markup, parse_mode='Markdown')

# Обработчик для возврата в главное меню
@bot.callback_query_handler(func=lambda call: call.data == "menu_back")
def handle_menu_back(call):
    """Возврат в главное меню"""
    if not bot:
        return
    
    show_main_menu(call.message)