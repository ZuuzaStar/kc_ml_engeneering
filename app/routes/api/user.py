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
from auth.basic import get_current_user, validate_password_strength



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
    User registration.

    Args:
        data: User registration data
        session: Database session

    Returns:
        dict: Success message
    """
    try:
        # Validate password strength
        if not validate_password_strength(data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase letters and numbers"
            )
        
        # Check if user already exists
        existing_user = UserService.get_user_by_email(data.email, session)
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        UserService.create_user(email=data.email, password=data.password, session=session, is_admin=data.is_admin)
        logger.info(f"New user registered: {data.email}")
        logger.info(f"Start bonus has been added: {data.email}")
        return {"message": "User successfully registered"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@user_route.post('/signin')
async def signin(data: UserSigninRequest, session=Depends(get_session)) -> Dict[str, str]:
    """
    User signin.

    Args:
        data: User signin data
        session: Database session

    Returns:
        dict: Success message
    """
    try:
        user = UserService.get_user_by_email(data.email, session)
        if not user:
            logger.warning(f"Failed login attempt for user: {data.email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials passed")
        
        if not UserService.verify_password(data.password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {data.email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials passed")
        
        return {"message": "User signed in successfully"}

    except Exception as e:
        logger.error(f"Error during signin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signin Error"
        )

@user_route.get('/balance')
async def get_balance(user: User = Depends(get_current_user), session=Depends(get_session)) -> Dict[str, float]:
    """
    Get wallet balance.

    Args:
        user: Current authenticated user
        session: Database session

    Returns:
        float: User balance
    """
    try:
        return {'Current balance': user.wallet.balance}
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error"
        )

@user_route.post('/balance/adjust')
async def adjust_balance(
    data: BalanceAdjustRequest, 
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> Dict[str, str]:
    """
    Adjust wallet balance with authentication.

    Args:
        data: Balance adjustment data
        user: Current authenticated user
        session: Database session

    Returns:
        dict: Success message
    """
    try:
        # Проверяем, что пользователь пытается изменить свой собственный баланс
        if user.email != data.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only adjust your own balance"
            )
        
        # Определяем тип транзакции в зависимости от прав пользователя
        transaction_type = TransactionType.ADMIN_ADJUSTMENT if user.is_admin else TransactionType.DEPOSIT
        
        WalletService.make_transaction(user.wallet, data.amount, transaction_type, session)
        logger.info(f"Successful balance adjustment for {user.email} (type: {transaction_type})")
        return {"message": "Successful balance adjustment"}

    except Exception as e:
        logger.error(f"Error during balance adjustment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Adjustment Error"
        )
    
@user_route.get("/transaction/history", response_model=List[Transaction])
async def get_transaction_history(
    user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[Transaction]:
    """
    Get transaction history for authenticated user.

    Args:
        user: Current authenticated user
        session: Database session

    Returns:
        List[Transaction]: List of user transactions
    """
    try:
        return user.wallet.transactions
    except Exception as e:
        logger.error(f"Error getting transaction history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting transaction history"
        )