from pydantic import BaseModel, Field
from enum import Enum
from .book_models import Book, BookPrice
from typing import Optional, List

class FeedBookStatus(str, Enum):
    BUY = "buy" #
    RENT_2WEEK = "rent_2week"
    RENT_MONTH = "rent_month"
    RENT_3MONTH = "rent_3month"
    RENT_END = "rent_end"
    READ_FREE= "read_free"

class FeedBook(BaseModel):
    book: Book = Field(..., description="Информация о книге")
    price: BookPrice = Field(..., description="Цены на книгу")
    open_for_read: bool = Field(..., description="Можно ли читать книгу")
    status: Optional[FeedBookStatus] = Field(..., description="Статус книги для пользователя")

class PaginatedFeedResponse(BaseModel):
    total: int = Field(..., description="Общее количество книг")
    page: int = Field(..., description="Текущая страница")
    limit: int = Field(..., description="Количество элементов на странице")
    books: List[FeedBook] = Field(..., description="Список книг в ленте")

class ReadBook(BaseModel):
    user_id: str = Field(..., description="Идентификатор пользователя")
    book_id: str = Field(..., description="Идентификатор книги")
    current_page: int = Field(..., ge=0, description="Текущая страница чтения")

