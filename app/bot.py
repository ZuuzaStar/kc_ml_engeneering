# app/telegram_bot.py
import os
import telebot
from telebot import types
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен. Пожалуйста, установите переменную окружения BOT_TOKEN.")
    raise ValueError("BOT_TOKEN не установлен.")

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}
