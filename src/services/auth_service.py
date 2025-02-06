import httpx
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status
from src.db.models.user_models import User, UserDB
from src.db.models.token_models import Token
from src.db.session import get_db
from src.core.config import settings
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from src.db.repositories.user_repo import UserRepository
# Загружаем переменные окружения
load_dotenv()

# Конфигурация Яндекс OAuth
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI")
YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USER_INFO_URL = "https://login.yandex.ru/info"

class AuthService:
    @staticmethod
    async def get_yandex_login_url():
        return f"{YANDEX_AUTH_URL}?response_type=code&client_id={YANDEX_CLIENT_ID}&redirect_uri={YANDEX_REDIRECT_URI}"

    @staticmethod
    async def get_yandex_token(code: str) -> Token:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                YANDEX_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": YANDEX_CLIENT_ID,
                    "client_secret": YANDEX_CLIENT_SECRET,
                    "redirect_uri": YANDEX_REDIRECT_URI,
                },
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не удалось получить токен",
                )
            token_data = response.json()
            return Token(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data["token_type"],
            )

    @staticmethod
    async def get_yandex_user_info(access_token: str) -> User:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                YANDEX_USER_INFO_URL,
                headers={"Authorization": f"OAuth {access_token}"},
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не удалось получить данные пользователя",
                )
            user_data = response.json()
            return User(
                id=user_data["id"],  # Используем ID от Яндекс
                login=user_data["default_email"],  # Используем email как логин
                email=user_data["default_email"],
                yandex_id=user_data["id"],
            )
    
    @staticmethod
    async def save_or_update_user(db: AsyncSession, yandex_id: str, login: str, email: str, access_token: str, refresh_token:str):
        # Проверяем, существует ли пользователь
        repo = UserRepository(db)
        user = await repo.get_user_by_yandex_id(yandex_id)

        if user:
            # Обновляем данные пользователя, если он уже существует
            user.login = login
            user.email = email
            user.access_token = access_token
            user.refresh_token = refresh_token
        else:
            # Создаем нового пользователя
            user = UserDB(yandex_id=yandex_id, login=login, email=email, access_token=access_token, refresh_token=refresh_token)
            created_user = await repo.create_user(user=user)
            # Создаём кошелёк с начальным балансом.
            await repo.create_user_wallet(user_id=created_user.id)
            return created_user
        return await repo.update_user(user=user)