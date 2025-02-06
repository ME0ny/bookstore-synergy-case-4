from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth_service import AuthService
from src.db.session import get_db
from src.db.models.user_models import User, UserDB
from src.db.models.token_models import Token
from src.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/yandex/login")
async def login_via_yandex():
    url = await AuthService.get_yandex_login_url()
    return RedirectResponse(url)

@router.get("/yandex/callback", response_model=Token)
async def yandex_callback(code: str, db: AsyncSession = Depends(get_db)):
    # Получаем токен
    token_data = await AuthService.get_yandex_token(code)
    access_token = token_data.access_token
    refresh_token = token_data.refresh_token
    # Получаем данные пользователя
    user_info = await AuthService.get_yandex_user_info(access_token)
    yandex_id = user_info.id
    login = user_info.login
    email = user_info.email
    # Сохраняем или обновляем пользователя в БД
    user = await AuthService.save_or_update_user(db, yandex_id, login, email, access_token, refresh_token)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.get("/users/me")
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "yandex_id": current_user.yandex_id,
        "login": current_user.login,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    }