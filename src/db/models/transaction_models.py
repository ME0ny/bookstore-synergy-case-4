from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.declarative import declarative_base
from src.db.models.user_models import User, UserDB
from src.db.models.book_models import Book, BookDB
from src.db.base import Base

class TransactionStatus(str, Enum):
    BUY = "buy"
    RENT_2WEEK = "rent_2week"
    RENT_MONTH = "rent_month"
    RENT_3MONTH = "rent_3month"

class UserTransaction(BaseModel):
    user_id: int = Field(..., description="Идентификатор пользователя")
    book_id: int = Field(..., description="Идентификатор книги")
    date_buy: datetime = Field(..., description="Дата покупки/аренды")
    price: int = Field(..., ge=0, description="Сумма транзакции")
    status: TransactionStatus = Field(..., description="Статус транзакции")

class TransactionResponse(BaseModel):
    message: str = Field(..., description="Статус операции")
    transaction: dict = Field(..., description="Детали транзакции")
    
class UserTransactionDB(Base):
    __tablename__ = "user_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    date_buy = Column(DateTime, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String, nullable=False)