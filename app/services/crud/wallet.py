from typing import TYPE_CHECKING
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Optional

# if TYPE_CHECKING:
from models.transaction import Transaction
from models.wallet import Wallet


def make_transaction(wallet: Wallet, transaction: "Transaction", session: Session) -> Wallet:
    """
    Изменить баланс кошелька.
    
    Args:
        wallet: кошелек пользователя
        transaction: транзакция, которую необхрдимо совершить
        session: экземпляр сесси БД
    
    Returns:
        Wallet: кошелек с добавленной транзакцией
    """
    try:
        wallet.transactions.append(transaction)
        wallet.balance += transaction.amount

        session.add(wallet)
        session.add(transaction)
        session.commit()
        session.refresh(transaction)

        return wallet
    
    except Exception as e:
        session.rollback()
        raise ValueError(f"Не удалось выполнить корректировку баланса: {e}") from e

def get_all_wallets(session: Session) -> Optional[List[Wallet]]:
    """
    Запрашивает всех пользователей из базы.
    
    Args:
        session: сессия базы данных
    
    Returns:
        List[Wallet]: Список пользователей
    """
    try:
        statement = select(Wallet).options(
            select(Wallet)
        )
        wallets = session.exec(statement).all()
        return wallets
    except Exception as e:
        raise

def get_wallet_by_id(wallet_id: int, session: Session) -> Optional[Wallet]:
    """
    Получить юзера по айдишнику.
    
    Args:
        wallet_id: ID юзера
        session: сессия базы данных
    
    Returns:
        Optional[Wallet]: Найденный пользователь или None
    """
    try:
        statement = select(Wallet).where(wallet.id == wallet_id).options(
            selectinload(wallet.transactions)
        )
        wallet = session.exec(statement).first()
        return wallet
    except Exception as e:
        raise

def create_wallet(wallet: Wallet, session: Session) -> Wallet:
    """
    Создание нового кошелька.
    
    Args:
        wallet: экземпляр нового кошелька
        session: сессия базы данных
    
    Returns:
        Wallet: новый коешелек
    """
    try:
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        return wallet
    except Exception as e:
        session.rollback()
        raise

def delete_wallet(wallet_id: int, session: Session) -> bool:
    """
    Удаление кошелька.
    
    Args:
        wallet_id: ID кошелька
        session: сессия базы данных
    
    Returns:
        bool: Удалился ли кошелек
    """
    try:
        wallet = get_wallet_by_id(wallet_id, session)
        if wallet:
            session.delete(wallet)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise
