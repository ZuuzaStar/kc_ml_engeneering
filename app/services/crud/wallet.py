from typing import TYPE_CHECKING
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from loguru import logger

# if TYPE_CHECKING:
from models.transaction import Transaction
from models.wallet import Wallet
from models.constants import TransactionType


def make_transaction(
    wallet: Wallet, 
    amount: float,
    type: TransactionType,
    description: str, 
    session: Session
) -> Wallet:
    """
    Совершить транзакцию по конкретному кошельку.

    Args:
        wallet: кошелек пользователя
        amount: сумма транзакции (списание - отрицательное значение / пополнение - положительное)
        type: тип транзакции
        description: описание транзакции в свободной форме
        session: экземпляр сессии БД
    
    Returns:
        Wallet: кошелек с добавленной транзакцией
    """
    # Проверяем, достаточно ли средств для списания
    if amount < 0 and wallet.balance + amount < 0:
        raise ValueError(f"Недостаточно средств. Баланс: {wallet.balance}, требуется: {abs(amount)}")
    
    try:
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            type=type,
            description=description, 
            wallet=wallet
        )
        
        wallet.transactions.append(transaction)
        wallet.balance += amount

        session.add(wallet)
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        session.refresh(wallet)

        logger.info(f"Транзакция выполнена: {amount} для кошелька {wallet.id}. Новый баланс: {wallet.balance}")
        return wallet
    
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при выполнении транзакции: {e}")
        raise ValueError(f"Не удалось выполнить транзакцию: {e}") from e


def get_all_wallets(session: Session) -> List[Wallet]:
    """
    Запрашивает все кошельки из базы.
    
    Args:
        session: сессия базы данных
    
    Returns:
        List[Wallet]: Список кошельков
    """
    try:
        statement = select(Wallet)
        wallets = session.exec(statement).all()
        return wallets
    except Exception as e:
        logger.error(f"Ошибка при получении всех кошельков: {e}")
        raise


def get_wallet_by_id(wallet_id: int, session: Session) -> Optional[Wallet]:
    """
    Получить кошелек по ID.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        Optional[Wallet]: Найденный кошелек или None
    """
    try:
        statement = select(Wallet).where(Wallet.id == wallet_id).options(
            selectinload(Wallet.transactions)
        )
        wallet = session.exec(statement).first()
        return wallet
    except Exception as e:
        logger.error(f"Ошибка при получении кошелька по ID {wallet_id}: {e}")
        raise


def get_wallet_by_user_id(user_id: int, session: Session) -> Optional[Wallet]:
    """
    Получить кошелек по ID пользователя.
    
    Args:
        user_id: ID пользователя
        session: сессия базы данных
    
    Returns:
        Optional[Wallet]: Найденный кошелек или None
    """
    try:
        statement = select(Wallet).where(Wallet.user_id == user_id).options(
            selectinload(Wallet.transactions)
        )
        wallet = session.exec(statement).first()
        return wallet
    except Exception as e:
        logger.error(f"Ошибка при получении кошелька пользователя {user_id}: {e}")
        raise


def create_wallet(wallet: Wallet, session: Session) -> Wallet:
    """
    Создание нового кошелька.
    
    Args:
        wallet: экземпляр нового кошелька
        session: сессия базы данных
    
    Returns:
        Wallet: новый кошелек
    """
    try:
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        logger.info(f"Кошелек {wallet.id} создан")
        return wallet
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании кошелька: {e}")
        raise


def delete_wallet(wallet_id: int, session: Session) -> bool:
    """
    Удаление кошелька.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        bool: True если кошелек удален, False если не найден
    """
    try:
        wallet = get_wallet_by_id(wallet_id, session)
        if wallet:
            session.delete(wallet)
            session.commit()
            logger.info(f"Кошелек {wallet_id} удален")
            return True
        logger.warning(f"Кошелек с ID {wallet_id} не найден")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении кошелька {wallet_id}: {e}")
        raise


def delete_all_wallets(session: Session) -> bool:
    """
    Удаление всех кошельков.
    
    Args:
        session: сессия базы данных
    
    Returns:
        bool: True если операция выполнена успешно
    """
    try:
        wallets = get_all_wallets(session)
        for wallet in wallets:
            session.delete(wallet)
        session.commit()
        logger.info(f"Удалено {len(wallets)} кошельков")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении всех кошельков: {e}")
        raise


def get_wallet_balance(wallet_id: int, session: Session) -> float:
    """
    Получить баланс кошелька.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        float: баланс кошелька
    """
    try:
        wallet = get_wallet_by_id(wallet_id, session)
        if wallet:
            return wallet.balance
        raise ValueError(f"Кошелек с ID {wallet_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении баланса кошелька {wallet_id}: {e}")
        raise


def get_wallet_transactions(wallet_id: int, session: Session) -> List[Transaction]:
    """
    Получить все транзакции кошелька.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        List[Transaction]: Список транзакций
    """
    try:
        wallet = get_wallet_by_id(wallet_id, session)
        if wallet:
            return wallet.transactions
        raise ValueError(f"Кошелек с ID {wallet_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении транзакций кошелька {wallet_id}: {e}")
        raise