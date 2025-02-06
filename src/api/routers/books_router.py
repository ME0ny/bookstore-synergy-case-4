from fastapi import APIRouter, Depends, HTTPException, status
from src.core.security import get_current_user
from src.db.models.user_models import UserDB
from src.db.models.book_models import FilterParams, BookPageResponse
from src.services.book_service import BookService
from src.db.models.feed_models import FeedBook, PaginatedFeedResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
import os

router = APIRouter(prefix="/books", tags=["books"])

@router.get("/feed", response_model=PaginatedFeedResponse)
async def get_filtered_feed_books(
    filters: FilterParams = Depends(),
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Возвращает отфильтрованную ленту книг для пользователя.

    :param filters: Параметры фильтрации.
    :param page: Номер страницы.
    :param limit: Количество элементов на странице.
    :return: Ответ с пагинированным списком книг.
    """
    book_service = BookService(db)
    total, feed_books = await book_service.get_filtered_feed_books(
        user=current_user,
        categories=filters.categories,
        authors=filters.authors,
        year_from=filters.year_from,
        year_to=filters.year_to,
        open_for_read=filters.open_for_read,
        page=page,
        limit=limit
    )

    return PaginatedFeedResponse(
        total=total,
        page=page,
        limit=limit,
        books=feed_books
    )

@router.get("/read/{book_id}/{page}", response_model=BookPageResponse)
async def read_book_page(
    book_id: int,
    page: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Читает страницу книги с проверкой прав доступа.
    
    :param book_id: ID книги.
    :param page: Номер страницы.
    :return: Содержимое страницы или ошибка.
    """
    book_service = BookService(db)
    page_data = await book_service.read_book_page(current_user.id, book_id, page)
    return BookPageResponse(page=page, content=page_data)