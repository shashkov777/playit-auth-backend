from typing import Union

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from src.jwt.tokens import verify_jwt_token
from src.repositories.users import UserRepository
from src.schemas.users import UserSchema


async def verify_user_by_jwt(request: Request, session: Session) -> UserSchema:
    """
    Возвращает пользователя после аутентификации по username с помощью jwt
    """
    token = request.cookies.get("jwt-token")
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    verified_token = verify_jwt_token(token)

    username = verified_token.get("sub")
    return UserRepository.get_user_by_username(session=session, username=username)
