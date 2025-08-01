import bcrypt
from models.user import User


def validate_password(user: User, password: str):
    """Проверяет что переданный пароль - верный"""
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise ValueError("Некорректный пароль")
    return True