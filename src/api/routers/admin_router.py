from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.models.book_models import PaginatedBooksResponse, BookWithPrice, Book, BookCreateRequest, BookPrice, BookPriceCreateRequest, BookDB, BookContentDB
from src.db.models.user_models import User, UserDB
from src.db.repositories.book_repo import BookRepository
from src.services.book_service import BookService
from src.db.repositories.content_repo import ContentRepository
from src.core.security import get_current_admin_user
from src.core.config import settings
import os
from datetime import datetime
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/books/", response_model=Book)
async def create_book(
    book: BookCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_admin_user)
):
    repo = BookRepository(db)
    db_book = await repo.create_book(book)
    return db_book

@router.post("/books/upload/")
async def upload_book(
    book_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_admin_user)
):
    print(book_id)
    # Проверяем допустимый формат файла (PDF или EPUB)
    if not file.filename.endswith((".pdf", ".epub")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый формат файла. Поддерживаются только PDF и EPUB."
        )

    # Проверяем, существует ли книга в базе
    repo = BookRepository(db)
    book = await repo.get_book_by_id(book_id)

    # Сохраняем файл в защищенной директории
    file_path = os.path.join(settings.PROTECTED_BOOKS_DIR, f"{book_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Сохраняем путь к файлу в таблице BookContent
    content_repo = ContentRepository(db)
    db_content = await content_repo.update_content(book_id=book_id, url_content=file_path)

    return {"message": "Файл книги успешно загружен", "content_id": db_content.id}

@router.patch("/books/{book_id}/update", response_model=Book)
async def update_book(
    book_id: int,
    updated_data: BookCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_admin_user)
):
    book_service = BookService(db)
    updated_book = await book_service.update_book(book_id, updated_data.dict(exclude_unset=True))
    return updated_book
 
@router.patch("/books/{book_id}/hide", response_model=Book)
async def hide_book(
    book_id: int,
    hidden_flag: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_admin_user)
):
    repo = BookRepository(db)
    db_book = await repo.hide_book(book_id, hidden_flag)
    return Book.from_orm(db_book)

@router.post("/books/{book_id}/prices/", response_model=BookPrice)
async def set_book_price(
    book_id: int,
    price: BookPriceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_admin_user)
):
    repo = BookRepository(db)
    db_price = await repo.set_book_price(book_id, price)
    return db_price

@router.get("/books", response_model=PaginatedBooksResponse)
async def get_books_with_prices_paginated(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_admin_user)
):
    """
    Возвращает книги с ценами с поддержкой пагинации.

    :param page: Номер страницы.
    :param limit: Количество элементов на странице.
    :return: Пагинированный список книг с ценами.
    """
    if limit > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Лимит не может превышать 100.")

    book_service = BookService(db)
    return await book_service.get_books_with_prices_paginated(page, limit)