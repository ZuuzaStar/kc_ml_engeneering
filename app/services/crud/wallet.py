from sqlmodel import Session, select
from typing import List, Optional
from loguru import logger
from models.transaction import Transaction
from models.wallet import Wallet
from models.constants import TransactionType
from services.crud import user as UserService


def make_transaction(
    wallet: Wallet, 
    amount: float,
    type: TransactionType,
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


def get_all_wallets(
    session: Session
) -> List[Wallet]:
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


def get_wallet_by_id(
    id: int, 
    session: Session
) -> Optional[Wallet]:
    """
    Получить кошелек по ID.
    
    Args:
        id: ID кошелька
        session: сессия базы данных
    
    Returns:
        Optional[Wallet]: Найденный кошелек или None
    """
    try:
        wallet = session.get(Wallet, id)
        return wallet
    except Exception as e:
        logger.error(f"Ошибка при получении кошелька по ID {id}: {e}")
        raise


def get_wallet_by_user_id(
    id: int, 
    session: Session
) -> Optional[Wallet]:
    """
    Получить кошелек по ID пользователя.
    
    Args:
        user_id: ID пользователя
        session: сессия базы данных
    
    Returns:
        Optional[Wallet]: Найденный кошелек или None
    """
    user = UserService.get_user_by_id(id)
    try:
        statement = select(Wallet).where(Wallet.user_id == user.id)
        wallet = session.exec(statement).first()
        return wallet
    except Exception as e:
        logger.error(f"Ошибка при получении кошелька пользователя {id}: {e}")
        raise

def get_wallet_balance(
    id: int, 
    session: Session
) -> float:
    """
    Получить баланс кошелька.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        float: баланс кошелька
    """
    try:
        wallet = get_wallet_by_id(id, session)
        if wallet:
            return wallet.balance
        raise ValueError(f"Кошелек с ID {id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении баланса кошелька {id}: {e}")
        raise


def get_wallet_transactions(
    id: int, 
    session: Session
) -> List[Transaction]:
    """
    Получить все транзакции кошелька.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        List[Transaction]: Список транзакций
    """
    try:
        wallet = get_wallet_by_id(id, session)
        if wallet:
            return wallet.transactions
        raise ValueError(f"Кошелек с ID {id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении транзакций кошелька {id}: {e}")
        raise