import os
import telebot
from telebot import types
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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

# Кэш авторизованных пользователей (telegram_id -> email)
authorized_users = {}

# Кэш учетных данных для BasicAuth (telegram_id -> {email, password})
user_credentials = {}

# ---------- HTTP API helpers ----------
def _get_auth(telegram_id):
    creds = user_credentials.get(telegram_id)
    if not creds:
        return None
    return httpx.BasicAuth(creds["email"], creds["password"])  # type: ignore[arg-type]

def api_signup(email: str, password: str) -> dict:
    url = f"{API_BASE_URL}/api/users/signup"
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json={"email": email, "password": password, "is_admin": False})
        return {"ok": resp.status_code in (200, 201), "status": resp.status_code, "data": resp.json() if resp.content else {}}

def api_signin(email: str, password: str) -> dict:
    url = f"{API_BASE_URL}/api/users/signin"
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json={"email": email, "password": password})
        return {"ok": resp.status_code == 200, "status": resp.status_code, "data": resp.json() if resp.content else {}}

def api_get_balance(telegram_id: int) -> dict:
    url = f"{API_BASE_URL}/api/users/balance"
    auth = _get_auth(telegram_id)
    if not auth:
        return {"ok": False, "status": 401, "data": {}}
    with httpx.Client(timeout=10.0, auth=auth) as client:
        resp = client.get(url)
        return {"ok": resp.status_code == 200, "status": resp.status_code, "data": resp.json() if resp.content else {}}

def api_get_prediction_history(telegram_id: int) -> dict:
    url = f"{API_BASE_URL}/api/events/prediction/history"
    auth = _get_auth(telegram_id)
    if not auth:
        return {"ok": False, "status": 401, "data": {}}
    with httpx.Client(timeout=20.0, auth=auth) as client:
        resp = client.get(url)
        return {"ok": resp.status_code == 200, "status": resp.status_code, "data": resp.json() if resp.content else []}

def api_create_prediction(telegram_id: int, message: str, top: int = 10) -> dict:
    url = f"{API_BASE_URL}/api/events/prediction/new"
    auth = _get_auth(telegram_id)
    if not auth:
        return {"ok": False, "status": 401, "data": {}}
    # FastAPI expects query params for primitive args unless Body is specified
    params = {"message": message, "top": top}
    with httpx.Client(timeout=60.0, auth=auth) as client:
        resp = client.post(url, params=params)
        return {"ok": resp.status_code == 200, "status": resp.status_code, "data": resp.json() if resp.content else []}

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
        if auth_type == "signup":
            result = handle_signup(email, password, user_id)
        else:
            result = handle_signin(email, password, user_id)

        if result['success']:
            cleanup_auth_states(chat_id)
            show_main_menu(message)
        else:
            bot.reply_to(message, f"❌ {result['message']}")
    except Exception as e:
        logger.error(f"Ошибка авторизации: {str(e)}")
        bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")
        cleanup_auth_states(chat_id)

def handle_signup(email, password, telegram_id):
    """Обработка регистрации через HTTP API"""
    try:
        resp = api_signup(email, password)
        if not resp["ok"]:
            # Конфликт 409 или другая ошибка
            detail = resp.get("data", {}).get("detail") if isinstance(resp.get("data"), dict) else None
            return {'success': False, 'message': detail or 'Ошибка регистрации.'}

        # Сохраняем учетные данные для последующих запросов
        user_credentials[telegram_id] = {"email": email, "password": password}
        authorized_users[telegram_id] = email
        logger.info(f"Пользователь {telegram_id} авторизован как {email}")
        return {'success': True, 'message': 'Регистрация успешна!'}
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        return {'success': False, 'message': 'Ошибка регистрации.'}

def handle_signin(email, password, telegram_id):
    """Обработка входа через HTTP API"""
    try:
        resp = api_signin(email, password)
        if not resp["ok"]:
            detail = resp.get("data", {}).get("detail") if isinstance(resp.get("data"), dict) else None
            return {'success': False, 'message': detail or 'Неверные учетные данные.'}

        user_credentials[telegram_id] = {"email": email, "password": password}
        authorized_users[telegram_id] = email
        logger.info(f"Пользователь {telegram_id} авторизован как {email}")
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
        email = authorized_users.get(user_id)
        if not email or user_id not in user_credentials:
            logger.warning(f"Пользователь {user_id} не авторизован, перенаправляем на /start")
            send_welcome(message)
            return

        balance_resp = api_get_balance(user_id)
        if not balance_resp["ok"]:
            logger.error(f"Не удалось получить баланс: {balance_resp['status']}")
            bot.reply_to(message, "❌ Ошибка загрузки меню.")
            return
        balance = balance_resp["data"].get("Current balance", 0)

        menu_text = (
            f"🎬 **Главное меню**\n\n"
            f"👤 Пользователь: {email}\n"
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
    
    # Удаляем из авторизованных и забываем учетные данные
    if user_id in authorized_users:
        del authorized_users[user_id]
    if user_id in user_credentials:
        del user_credentials[user_id]
    
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
        if user_id not in authorized_users or user_id not in user_credentials:
            bot.reply_to(message, "❌ Необходимо авторизоваться.")
            return

        bot.reply_to(message, "⏳ Обрабатываю ваш запрос...")

        # Выполняем запрос к API для получения рекомендаций
        pred_resp = api_create_prediction(user_id, input_text, top=10)
        if not pred_resp["ok"]:
            if pred_resp["status"] == 402:
                # Недостаточно средств
                balance_resp = api_get_balance(user_id)
                balance = balance_resp["data"].get("Current balance", 0) if balance_resp["ok"] else "N/A"
                bot.reply_to(message, f"❌ Недостаточно средств. Ваш баланс: {balance}. Пополните баланс через веб-интерфейс.")
                return
            logger.error(f"Ошибка предсказания: {pred_resp['status']}")
            bot.reply_to(message, "❌ Ошибка при обработке запроса. Попробуйте позже.")
            return

        movies = pred_resp["data"] or []
        if not movies:
            bot.reply_to(message, "❌ К сожалению, не удалось найти подходящие фильмы.")
            return

        # Получаем актуальный баланс после списания
        balance_resp = api_get_balance(user_id)
        new_balance = balance_resp["data"].get("Current balance", "N/A") if balance_resp["ok"] else "N/A"

        response_text = f"🎬 Найдено {len(movies)} фильмов по запросу: '{input_text}'\n\n"
        for i, movie in enumerate(movies, 1):
            title = movie.get("title", "Без названия")
            year = movie.get("year", "N/A")
            genres = movie.get("genres") or []
            response_text += f"{i}. **{title}** ({year})\n"
            response_text += f"   Жанры: {', '.join(genres[:3]) if genres else 'Не указаны'}\n\n"

        response_text += f"💳 Текущий баланс: {new_balance}"

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_back"))

        bot.reply_to(message, response_text, reply_markup=markup, parse_mode='Markdown')
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
        if user_id not in authorized_users or user_id not in user_credentials:
            bot.reply_to(message, "❌ Необходимо авторизоваться.")
            return

        hist_resp = api_get_prediction_history(user_id)
        if not hist_resp["ok"]:
            logger.error(f"Ошибка получения истории: {hist_resp['status']}")
            bot.reply_to(message, "❌ Произошла ошибка при получении истории.")
            return

        predictions = hist_resp["data"] or []
        if not predictions:
            bot.reply_to(message, "📚 У вас пока нет истории рекомендаций.")
            return

        response = "📚 Ваша история рекомендаций:\n\n"
        for i, pred in enumerate(predictions[-5:], 1):
            input_text = (pred.get("input_text") or "")[:50]
            cost = pred.get("cost", "N/A")
            timestamp = pred.get("timestamp", "")
            movies = pred.get("movies") or []
            response += f"{i}. {input_text}...\n"
            response += f"   💰 Стоимость: {cost} кредитов\n"
            response += f"   📅 Дата: {timestamp.replace('T', ' ')[:16] if isinstance(timestamp, str) else 'N/A'}\n"
            response += f"   🎬 Фильмов: {len(movies)}\n\n"

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
        if user_id not in authorized_users or user_id not in user_credentials:
            bot.reply_to(message, "❌ Необходимо авторизоваться.")
            return

        balance_resp = api_get_balance(user_id)
        if not balance_resp["ok"]:
            logger.error(f"Ошибка получения баланса: {balance_resp['status']}")
            bot.reply_to(message, "❌ Произошла ошибка при получении баланса.")
            return

        balance = balance_resp["data"].get("Current balance", 0)
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
        if user_id not in authorized_users or user_id not in user_credentials:
            bot.reply_to(message, "❌ Необходимо авторизоваться.")
            return

        balance_resp = api_get_balance(user_id)
        if not balance_resp["ok"]:
            logger.error(f"Ошибка получения баланса: {balance_resp['status']}")
            bot.reply_to(message, "❌ Произошла ошибка при получении баланса.")
            return

        balance = balance_resp["data"].get("Current balance", 0)
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