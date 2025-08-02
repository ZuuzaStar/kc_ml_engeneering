from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.database import get_session
from models.transaction import Transaction 
from typing import List

transaction_router = APIRouter()
transactions = []

@transaction_router.get("/", response_model=List['Transaction']) 
async def retrieve_all_transactions() -> List['Transaction']:
    return transactions

@transaction_router.get("/{id}", response_model=Transaction) 
async def retrieve_transaction(id: int) -> Transaction:
    for transaction in transactions: 
        if transaction.id == id:
            return transaction 
    raise HTTPException(status_code=status. HTTP_404_NOT_FOUND, detail="Transaction with supplied ID does not exist")

@transaction_router.post("/new")
async def create_transaction(body: Transaction = Body(...)) -> dict: 
    transactions.append(body)
    return {"message": "Transaction created successfully"}

@transaction_router.delete("/{id}")
async def delete_transaction(id: int) -> dict: 
    for transaction in transactions:
        if transaction.id == id: 
            transactions.remove(transaction)
            return {"message": "Transaction deleted successfully"}
        raise HTTPException(status_code=status. HTTP_404_NOT_FOUND, detail="Transaction with supplied ID does not exist")

@transaction_router.delete("/")
async def delete_all_transactions() -> dict: 
    transactions.clear()
    return {"message": "Transactions deleted successfully"}