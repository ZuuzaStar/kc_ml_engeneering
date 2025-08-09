from models.user import User
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import bcrypt
from sqlalchemy import delete


def make_user_admin(user: User, session: Session) -> User:
    """
    Наделяет юзера правами администратора.
    
    Args:
        user: объект текущего пользователя
        session: сессия базы данных
    
    Returns:
        User: обновленный экземпляр юзера
    """
    user.is_admin = True
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise ValueError(f"Не удалось обновить даннве пользователя: {e}") from e

def get_all_users(session: Session) -> Optional[List[User]]:
    """
    Запрашивает всех пользователей из базы.
    
    Args:
        session: сессия базы данных
    
    Returns:
        List[User]: Список пользователей
    """
    try:
        statement = select(User)
        users = session.exec(statement).all()
        return users
    except Exception as e:
        raise

def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    """
    Получить юзера по айдишнику.
    
    Args:
        user_id: ID юзера
        session: сессия базы данных
    
    Returns:
        Optional[User]: Найденный пользователь или None
    """
    try:
        statement = select(User).where(User.id == user_id).options(
            selectinload(User.wallet),
            selectinload(User.predictions)
        )
        user = session.exec(statement).first()
        return user
    except Exception as e:
        raise

def get_user_by_email(email: str, session: Session) -> Optional[User]:
    """
    Получить юзера по email.
    
    Args:
        email: email юзера
        session: сессия базы данных
    
    Returns:
        Optional[User]: Найденный пользователь или None
    """
    try:
        statement = select(User).where(User.email == email).options(
            selectinload(User.predictions)
        )
        user = session.exec(statement).first()
        return user
    except Exception as e:
        raise

def create_user(user: User, session: Session) -> User:
    """
    Регистрация нового пользователя.
    
    Args:
        user: экземпляр нового пользователя
        session: сессия базы данных
    
    Returns:
        User: новый пользователь
    """
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise

def delete_user(user_id: int, session: Session) -> bool:
    """
    Удаление пользователя.
    
    Args:
        user: экземпляр нового пользователя
        session: сессия базы данных
    
    Returns:
        User: новый пользователь
    """
    try:
        user = get_user_by_id(user_id, session)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise

def delete_all_users(session: Session) -> bool:
    """
    Удаление всех пользователей.
    """
    try:
        delete_statement = delete(User)
        session.exec(delete_statement)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()