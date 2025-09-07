from datetime import datetime, timedelta
from fastapi_users.jwt import generate_jwt, decode_jwt
from fastapi import HTTPException
from src.utils.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


def create_jwt_token(username: str, telegram_id: int) -> str:
    """
    Синхронно создаёт JWT-токен на основе username и telegram_id.
    """
    try:
        payload = {
            "sub": username,
            "telegram_id": telegram_id,
            "aud": "prod",  # fastapi-users.jwt требует дополнительный аргумент audience
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return generate_jwt(payload, SECRET_KEY)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации токена: {str(e)}")


def verify_jwt_token(token: str) -> dict:
    """
    Синхронно декодирует и проверяет JWT-токен.
    """
    try:
        audience = "prod"  # Должно совпадать с "aud" в create_jwt_token
        return decode_jwt(token, SECRET_KEY, audience)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Невалидный токен: {str(e)}")
