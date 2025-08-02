from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.transaction import Transaction
    from models.user import Wallet


def make_transaction(wallet: "Wallet", transaction: "Transaction"):
    wallet.transactions.append(transaction)
    wallet.balance += transaction.amount