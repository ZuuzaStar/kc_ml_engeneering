from fastapi import APIRouter, HTTPException, status, Depends
from  database.database import get_session
from typing import List, Dict
import logging
from models.user import User
from models.wallet import Wallet
from models.transaction import Transaction
from models.constants import TransactionCost, TransactionType
from services.crud import user as UserService
from services.crud import wallet as WalletService



# Configure logging
logger = logging.getLogger(__name__)

user_route = APIRouter()

@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with email and password")
async def signup(data: User, session=Depends(get_session)) -> Dict[str, str]:
    """
    Create new user account.

    Args:
        data: User registration data
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If user already exists
    """
    try:
        if UserService.get_user_by_email(data.email, session):
            logger.warning(f"Signup attempt with existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        # Сначала создаем пустой кошелек
        wallet = Wallet()
    
        # Потом создаем пользователя c этим кошельком
        user = User(
            email=data.email,
            password_hash=UserService.hash_password(data.password),
            wallet_id=wallet.id,
            wallet=wallet
        )
        # Персонализируем кошелек
        wallet.user_id = user.id

        WalletService.create_wallet(wallet,session)
        UserService.create_user(user, session)
        logger.info(f"New user registered: {data.email}")
        
        user_bonus = Transaction(
            user_id=user.id,
            wallet_id=wallet.id,
            amount=TransactionCost.BONUS.value,
            type=TransactionType.DEPOSIT,
            description="Приветственный бонус при регистрации"
        )
        WalletService.make_transaction(wallet, user_bonus, session)
        logger.info(f"Start bonus add: {data.email}")
        return {"message": "User successfully registered"}

    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@user_route.post('/signin')
async def signin(data: User, session=Depends(get_session)) -> Dict[str, str]:
    """
    Authenticate existing user.

    Args:
        form_data: User credentials
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If authentication fails
    """
    user = UserService.get_user_by_email(data.email, session)
    if user is None:
        logger.warning(f"Login attempt with non-existent email: {data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
    
    if user.password != UserService.hash_password(data.password):
        logger.warning(f"Failed login attempt for user: {data.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials passed")
    
    return {"message": "User signed in successfully"}

@user_route.get('/balance')
async def get_balance(data: User, session=Depends(get_session)) -> Dict[str, float]:
    """
    Get wallet balance.

    Args:
        form_data: User credentials
        session: Database session

    Returns:
        float: User balance
    """
    try:
        user = UserService.get_user_by_email(data.email, session)
        if not user:
            logger.warning(f"Wrong email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email does not exists"
            )
        return {'Current balance': user.wallet.balance}
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error"
        )
    
@user_route.get('/balance/adjust')    
async def adjust_balance(data: User, amount: float, session=Depends(get_session)) -> Dict[str, str]:
    """
    Adjust wallet balance.

    Args:
        data: User registration data
        session: Database session

    Returns:
        dict: Success message
    """
    try:
        user = UserService.get_user_by_email(data.email, session)
        if not user:
            logger.warning(f"Wrong email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email does not exists"
            )
        
        transaction = Transaction(
            user_id=user.id,
            wallet_id=user.wallet_id,
            amount=TransactionCost(amount).value,
            type=TransactionType.DEPOSIT,
            description="Пополнение кошелька"
        )
        WalletService.make_transaction(user.wallet, transaction, session)
        logger.info(f"Successfull balance adjustment: {data.email}")
        return {"message": "Successfull balance adjustment"}

    except Exception as e:
        logger.error(f"Error during adjustment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Adjustment Error"
        )
    
@user_route.get("/transaction/history", response_model=List[Transaction]) 
async def get_transaction_history(
    data: User, 
    session=Depends(get_session)
    ) -> List[Transaction]:
    user = UserService.get_user_by_email(data.email, session)
    predictions = user.wallet.transactions
    return predictions