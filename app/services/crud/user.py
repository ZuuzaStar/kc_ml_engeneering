from models.user import User
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import bcrypt
from sqlalchemy import delete
from models.wallet import Wallet
from models.transaction import Transaction
from models.constants import TransactionCost, TransactionType
from services.crud.wallet import make_transaction
from loguru import logger


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
        logger.info(f"Пользователь {user.email} получил права администратора")
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"Не удалось обновить данные пользователя: {e}")
        raise ValueError(f"Не удалось обновить данные пользователя: {e}") from e


def get_all_users(session: Session) -> List[User]:
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
        logger.error(f"Ошибка при получении всех пользователей: {e}")
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
        logger.error(f"Ошибка при получении пользователя по ID {user_id}: {e}")
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
        logger.error(f"Ошибка при получении пользователя по email {email}: {e}")
        raise


def create_user(
    email: str, 
    password_hash: str, 
    session: Session,
    is_admin: bool = False
) -> User:
    """
    Регистрация нового пользователя.
    
    Args:
        email: email пользователя
        password_hash: хеш пароля
        session: сессия базы данных
        is_admin: является ли администратором
    
    Returns:
        User: новый пользователь
    """
    existing_user = get_user_by_email(email, session)
    if existing_user:
        raise ValueError("Пользователь с таким email уже существует")
    
    try:
        wallet = Wallet()
        session.add(wallet)

        user = User(
            email=email, 
            password_hash=password_hash,
            wallet=wallet,
            is_admin=is_admin
        )
        wallet.user = user
        wallet.user_id = user.id

        # Создаем пользователя
        session.add(user)
        session.commit()
        session.refresh(wallet)
        session.refresh(user)

        # Добавляем приветственный бонус
        make_transaction(
            user.wallet, 
            TransactionCost.BONUS.value, 
            TransactionType.DEPOSIT,
            description="Приветственный бонус при регистрации"
        )
        
        logger.info(f"Пользователь {user.email} создан")
        return user
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании пользователя {email}: {e}")
        raise


def delete_user(user_id: int, session: Session) -> bool:
    """
    Удаление пользователя.
    
    Args:
        user_id: ID пользователя для удаления
        session: сессия базы данных
    
    Returns:
        bool: True если пользователь удален, False если не найден
    """
    try:
        user = get_user_by_id(user_id, session)
        if user:
            session.delete(user)
            session.commit()
            logger.info(f"Пользователь {user.email} удален")
            return True
        logger.warning(f"Пользователь с ID {user_id} не найден")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
        raise


def delete_all_users(session: Session) -> bool:
    """
    Удаление всех пользователей.
    
    Args:
        session: сессия базы данных
    
    Returns:
        bool: True если операция выполнена успешно
    """
    try:
        delete_statement = delete(User)
        session.exec(delete_statement)
        session.commit()
        logger.info("Все пользователи удалены")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении всех пользователей: {e}")
        raise


def create_demo_users(session: Session) -> None:
    """Создание демо пользователей"""
    demo_users = [
        ("user@example.com", "user123", False),
        ("admin@example.com", "admin123", True)
    ]

    for email, password, is_admin in demo_users:
        try:
            if not get_user_by_email(email, session):
                create_user(
                    email=email, 
                    password_hash=hash_password(password), 
                    session=session, 
                    is_admin=is_admin
                )
            else:
                logger.info(f"Пользователь {email} уже существует")
        except Exception as e:
            logger.error(f"Ошибка при создании демо пользователя {email}: {e}")
    
    logger.info("Демо пользователи созданы")


def hash_password(password: str) -> str:
    """
    Хеширование пароля с использованием bcrypt.
    
    Args:
        password: исходный пароль
    
    Returns:
        str: хешированный пароль
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Проверка пароля.
    
    Args:
        password: исходный пароль
        hashed_password: хешированный пароль
    
    Returns:
        bool: True если пароль верный
    """
    return bcrypt.checkpw(password.encode(), hashed_password.encode())