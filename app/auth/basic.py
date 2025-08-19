from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session
from services.crud import user as UserService
from database.database import get_session

security = HTTPBasic()

def get_current_user(
    creds: HTTPBasicCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = UserService.get_user_by_email(creds.username, session)
    if not user or not UserService.verify_password(creds.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user