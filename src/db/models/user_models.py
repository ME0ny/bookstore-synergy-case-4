from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from src.db.base import Base

class User(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор пользователя")
    login: EmailStr = Field(..., description="Логин пользователя (email)")
    hashed_password: Optional[str] = Field(None, min_length=8, description="Хэшированный пароль пользователя")
    is_admin: bool = Field(default=False, description="Является ли пользователь администратором")
    yandex_id: Optional[str] = Field(None, description="ID пользователя в Яндекс OAuth")
    email: Optional[EmailStr] = Field(None, description="Email пользователя")

class UserAuth(BaseModel):
    user_id: str = Field(..., description="Идентификатор пользователя")
    refresh_token: Optional[str] = Field(None, description="Refresh токен для обновления access токена")

class UserWallet(BaseModel):
    user_id: str = Field(..., description="Идентификатор пользователя")
    account: int = Field(..., ge=0, description="Баланс пользователя в виртуальных рублях")

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    yandex_id = Column(String, unique=True, nullable=False)
    login = Column(String, nullable=False)
    email = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    access_token = Column(String)
    refresh_token = Column(String)
    wallet = relationship("UserWalletDB", back_populates="user", uselist=False)  # Связь с кошельком

class UserWalletDB(Base):
    __tablename__ = "user_wallet"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    account = Column(Integer, default=1000)  # Начальный баланс
    user = relationship("UserDB", back_populates="wallet")