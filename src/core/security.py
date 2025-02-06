from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from src.db.models.user_models import UserDB
from src.db.session import AsyncSessionLocal
from sqlalchemy.future import select
from src.core.config import settings
import httpx
import logging
from functools import lru_cache

# OAuth2 схема для получения токена из запроса
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Получает текущего пользователя на основе токена."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )

    # Проверяем валидность токена (локально или через API)
    user_info = await verify_yandex_token(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
        )

    async with AsyncSessionLocal() as session:
        # Ищем пользователя по yandex_id
        result = await session.execute(
            select(UserDB).where(UserDB.yandex_id == user_info['id'])
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        return user

async def verify_yandex_token(token: str) -> dict:
    """Проверяет валидность токена через Yandex API или локально (если это JWT)."""
    try:
        # Пытаемся декодировать JWT локально (если это возможно)
        try:
            payload = jwt.decode(
                token,
                settings.YANDEX_CLIENT_SECRET,
                algorithms=["RS256"],
                audience=settings.YANDEX_CLIENT_ID  # Убедитесь, что аудитория совпадает с вашим client_id
            )
            return payload  # Возвращаем декодированные данные из JWT

        except JWTError as e:
            print(f"Не удалось декодировать JWT: {e}. Проверяем через API.")

        # Если это не JWT или декодирование не удалось, проверяем через API Yandex
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://login.yandex.ru/info",
                headers={"Authorization": f"OAuth {token}"}
            )
            response.raise_for_status()  # Проверяем статус ответа

            return response.json()

    except httpx.HTTPError as e: 
        return None

async def get_current_admin_user(current_user: UserDB = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return current_user