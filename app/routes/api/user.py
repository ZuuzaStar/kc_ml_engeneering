from fastapi import APIRouter, HTTPException, status, Depends
from  database.database import get_session
from typing import List, Dict
import logging
from models.user import User
from models.wallet import Wallet
from models import UserSignupRequest, UserSigninRequest, UserEmailRequest, BalanceAdjustRequest
from models.transaction import Transaction
from models.constants import TransactionCost, TransactionType
from services.crud import user as UserService
from services.crud import wallet as WalletService
from auth.basic import get_current_user



# Configure logging
logger = logging.getLogger(__name__)

user_route = APIRouter()

@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with email and password")
async def signup(data: UserSignupRequest, session=Depends(get_session)) -> Dict[str, str]:
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
        UserService.create_user(email=data.email, password=data.password, session=session)
        logger.info(f"New user registered: {data.email}")
        logger.info(f"Start bonus has been added: {data.email}")
        return {"message": "User successfully registered"}

    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@user_route.post('/signin')
async def signin(data: UserSigninRequest, session=Depends(get_session)) -> Dict[str, str]:
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
    
    if not UserService.verify_password(data.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {data.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials passed")
    
    return {"message": "User signed in successfully"}

@user_route.get('/balance')
async def get_balance(data: UserEmailRequest, session=Depends(get_session)) -> Dict[str, float]:
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
    
@user_route.post('/balance/adjust')
async def adjust_balance(data: BalanceAdjustRequest, session=Depends(get_session)) -> Dict[str, str]:
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
        WalletService.make_transaction(user.wallet, data.amount, TransactionType.ADMIN_ADJUSTMENT, session)
        logger.info(f"Successfull balance adjustment for {user.email}")
        return {"message": "Successfull balance adjustment"}

    except Exception as e:
        logger.error(f"Error during adjustment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Adjustment Error"
        )
    
@user_route.get("/transaction/history", response_model=List[Transaction]) 
async def get_transaction_history(
    data: UserEmailRequest, 
    session=Depends(get_session)
    ) -> List[Transaction]:
    user = UserService.get_user_by_email(data.email, session)
    predictions = user.wallet.transactions
    return predictions

@user_route.get('/balance-auth')
async def get_balance_auth(
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> Dict[str, float]:
    user = UserService.get_user_by_email(user.email, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    return {"Current balance": user.wallet.balance}

@user_route.get("/transaction/history-auth", response_model=List[Transaction])
async def get_transaction_history_auth(
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[Transaction]:
    user = UserService.get_user_by_email(user.email, session)
    return user.wallet.transactions