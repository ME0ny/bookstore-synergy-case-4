from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ARRAY, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from src.db.base import Base

class Book(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор книги")
    title: str = Field(..., min_length=1, description="Название книги")
    url_img: str = Field(..., description="Ссылка на обложку книги")
    category: List[str] = Field(..., description="Категории книги")
    author: List[str] = Field(..., description="Авторы книги")
    year_of_create: datetime = Field(..., description="Год создания книги")
    hidden: bool = Field(default=False, description="Скрыта ли книга от пользователей")

class BookContent(BaseModel):
    book_id: int = Field(..., description="Идентификатор книги")
    url_content: str = Field(..., description="Ссылка на контент книги")

class BookPrice(BaseModel):
    book_id: int = Field(..., description="Идентификатор книги")
    price: Optional[int] = Field(None, ge=0, description="Цена покупки книги")
    price_rent_2week: Optional[int] = Field(None, ge=0, description="Цена аренды на 2 недели")
    price_rent_month: Optional[int] = Field(None, ge=0, description="Цена аренды на месяц")
    price_rent_3month: Optional[int] = Field(None, ge=0, description="Цена аренды на 3 месяца")

class BookCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Название книги")
    url_img: str = Field(..., description="Ссылка на обложку книги")
    category: List[str] = Field(..., description="Категории книги")
    author: List[str] = Field(..., description="Авторы книги")
    year_of_create: datetime = Field(..., description="Год создания книги")
    hidden: bool = Field(default=False, description="Скрыта ли книга от пользователей")

class BookPriceCreateRequest(BaseModel):
    book_id: int = Field(..., description="Идентификатор книги")
    price: Optional[int] = Field(None, ge=0, description="Цена покупки книги")
    price_rent_2week: Optional[int] = Field(None, ge=0, description="Цена аренды на 2 недели")
    price_rent_month: Optional[int] = Field(None, ge=0, description="Цена аренды на месяц")
    price_rent_3month: Optional[int] = Field(None, ge=0, description="Цена аренды на 3 месяца")

class BookWithPrice(BaseModel):
    book: Book = Field(..., description="Информация о книге")
    price: Optional[int] = Field(None, ge=0, description="Цена покупки книги")
    price_rent_2week: Optional[int] = Field(None, ge=0, description="Цена аренды на 2 недели")
    price_rent_month: Optional[int] = Field(None, ge=0, description="Цена аренды на месяц")
    price_rent_3month: Optional[int] = Field(None, ge=0, description="Цена аренды на 3 месяца")

class PaginatedBooksResponse(BaseModel):
    total: int = Field(..., description="Общее количество книг")
    page: int = Field(..., description="Текущая страница")
    limit: int = Field(..., description="Количество элементов на странице")
    books: List[BookWithPrice] = Field(..., description="Список книг с ценами")

class FilterParams(BaseModel):
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    open_for_read: Optional[bool] = None

class BookPageResponse(BaseModel):
    page: int = Field(..., description="Номер страницы")
    content: str = Field(..., description="Текстовое содержимое страницы")
    
class BookDB(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url_img = Column(String, nullable=False)
    category = Column(ARRAY(String), nullable=False)
    author = Column(ARRAY(String), nullable=False)
    year_of_create = Column(DateTime, nullable=False)
    hidden = Column(Boolean, default=False)

    prices = relationship("BookPriceDB", backref="book", uselist=False)

class BookPriceDB(Base):
    __tablename__ = "book_prices"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    price = Column(Integer, nullable=True)
    price_rent_2week = Column(Integer, nullable=True)
    price_rent_month = Column(Integer, nullable=True)
    price_rent_3month = Column(Integer, nullable=True)

class BookContentDB(Base):
    __tablename__ = "book_content"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    url_content = Column(String, nullable=False)

