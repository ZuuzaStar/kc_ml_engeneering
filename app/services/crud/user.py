import bcrypt
from models.user import User
from models.transaction import Transaction
from services.crud.wallet import make_transaction
from models.constants import TransactionType, TransactionCost
from sqlmodel import Session, select
from typing import List


def validate_password(user: User, password: str):
    """Проверяет что переданный пароль - верный"""
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise ValueError("Некорректный пароль")
    return True

def make_user_admin(user: User, target_user: User):
    if not user.is_admin:
        raise ValueError("Для этого действия нужны права администратора")
    target_user.is_admin = True

def adjust_balance(user: User, target_user: User, amount: float, description: str) -> 'Transaction':
    if not user.is_admin:
        raise ValueError("Для этого действия нужны права администратора")
    make_transaction(
        wallet=target_user.wallet,
        transaction = Transaction(
            user_id=target_user.id,
            wallet_id=target_user.wallet.id,
            amount=TransactionCost(amount).value,
            type=TransactionType.ADMIN_ADJUSTMENT,
            description=description
        )
    )

def get_all_users(session: Session) -> List[User]:
    """
    Retrieve all users with their events.
    
    Args:
        session: Database session
    
    Returns:
        List[User]: List of all users
    """
    try:
        statement = select(User).options(
            select(User)
        )
        users = session.exec(statement).all()
        return users
    except Exception as e:
        raise