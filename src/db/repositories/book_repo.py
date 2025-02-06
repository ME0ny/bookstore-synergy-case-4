from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func
from src.db.models.book_models import Book, BookDB, BookCreateRequest, BookPriceDB, BookPriceCreateRequest, BookContentDB
from fastapi import HTTPException, status
from typing import Optional

class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_book(self, book: BookCreateRequest):
        db_book = BookDB(
            title=book.title,
            url_img=book.url_img,
            category=book.category,
            author=book.author,
            year_of_create=book.year_of_create,
            hidden=book.hidden
        )
        self.db.add(db_book)
        await self.db.commit()
        await self.db.refresh(db_book)
        # Автоматически создаем запись в book_prices с дефолтными значениями
        db_price = BookPriceDB(
            book_id=db_book.id,  # Используем ID только что созданной книги
            price=0,
            price_rent_2week=0,
            price_rent_month=0,
            price_rent_3month=0
        )
        self.db.add(db_price)
        await self.db.commit()
        await self.db.refresh(db_price)
        #Автоматически создаем запись в book_content с дефолтными значениями
        db_content = BookContentDB(book_id=db_book.id, url_content="")
        self.db.add(db_content)
        await self.db.commit()
        await self.db.refresh(db_content)
        return db_content
        return db_book
    
    async def update_book(self, book_id: int, updated_data: dict) -> BookDB:
        """
        Обновляет информацию о книге в базе данных.

        :param book_id: ID книги.
        :param updated_data: Словарь с новыми данными для обновления.
        :return: Обновленную книгу.
        """
        # Получаем текущую книгу из базы данных
        result = await self.db.execute(select(BookDB).where(BookDB.id == book_id))
        book = result.scalars().first()
        if not book:
            raise HTTPException(status_code=404, detail="Книга не найдена")

        # Обновляем поля книги
        for key, value in updated_data.items():
            if hasattr(book, key):
                setattr(book, key, value)

        # Сохраняем изменения в базе данных
        self.db.add(book)
        await self.db.commit()
        await self.db.refresh(book)

        return book

    async def hide_book(self, book_id: int, hidden_flag: bool = True) -> BookDB:
        # Находим книгу по ID
        result = await self.db.execute(select(BookDB).where(BookDB.id == book_id))
        db_book = result.scalars().first()
        if not db_book:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        # Устанавливаем hidden в True
        db_book.hidden = hidden_flag
        await self.db.commit()
        await self.db.refresh(db_book)
        return db_book
    
    async def set_book_price(self, book_id: int, price: BookPriceCreateRequest):
        # Находим запись по book_id
        result = await self.db.execute(select(BookPriceDB).where(BookPriceDB.book_id == book_id))
        db_price = result.scalars().first()

        # Если запись не найдена, выбрасываем исключение
        if not db_price:
            raise HTTPException(status_code=404, detail="Цены для книги не найдены")

        # Обновляем поля
        db_price.price = price.price
        db_price.price_rent_2week = price.price_rent_2week
        db_price.price_rent_month = price.price_rent_month
        db_price.price_rent_3month = price.price_rent_3month

        # Сохраняем изменения
        await self.db.commit()
        await self.db.refresh(db_price)

        return db_price

    async def get_book_by_id(self, book_id: int) -> BookDB: 
        result = await self.db.execute(select(BookDB).where(BookDB.id == book_id))
        book = result.scalars().first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Книга с указанным ID не найдена."
            )
        return book
    
    async def get_book_price_by_id(self, book_id: int):
        """Получить цену книги по ID."""
        result = await self.db.execute(select(BookPriceDB).where(BookPriceDB.book_id == book_id))
        return result.scalars().first()
    
    async def get_all_books_with_prices(self):
        """
        Возвращает список всех книг вместе с их ценами.

        :return: Список кортежей (BookDB, BookPriceDB).
        """
        result = await self.db.execute(
            select(BookDB, BookPriceDB)
            .outerjoin(BookPriceDB, BookDB.id == BookPriceDB.book_id)
        )
        return result.all()

    async def get_books_with_prices_paginated(
        self,
        page: int = 1,
        limit: int = 10
    ):
        """
        Возвращает книги с ценами с поддержкой пагинации.
        
        :param page: Номер страницы.
        :param limit: Количество элементов на странице.
        :return: Список книг с ценами и общее количество книг.
        """
        offset = (page - 1) * limit

        # Получаем общее количество книг
        total_query = await self.db.execute(select(func.count()).select_from(BookDB))
        total = total_query.scalar()
        if total is None:
            total = 0

        # Получаем книги с ценами для текущей страницы
        query = (
            select(BookDB)
            .outerjoin(BookPriceDB, BookDB.id == BookPriceDB.book_id)
            .options(joinedload(BookDB.prices))  # Загружаем связанные данные о ценах
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        books = result.unique().scalars().all()  # Получаем только объекты BookDB

        return total, books

    async def get_filtered_books(
        self,
        categories: Optional[list[str]] = None,
        authors: Optional[list[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        open_for_read: Optional[bool] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10
    ):
        """
        Возвращает книги с поддержкой фильтрации и пагинации.

        :param categories: Список категорий для фильтрации.
        :param authors: Список авторов для фильтрации.
        :param year_from: Минимальный год написания.
        :param year_to: Максимальный год написания.
        :param open_for_read: Фильтр по доступности для чтения.
        :param user_id: ID пользователя для проверки доступности книг.
        :param page: Номер страницы.
        :param limit: Количество элементов на странице.
        :return: Список книг с ценами и общее количество книг.
        """
        offset = (page - 1) * limit

        query = (
            select(BookDB)
            .outerjoin(BookPriceDB, BookDB.id == BookPriceDB.book_id)
            .options(joinedload(BookDB.prices))
        )

        # Фильтрация по категориям
        if categories:
            query = query.filter(BookDB.category.overlap(categories))

        # Фильтрация по авторам
        if authors:
            query = query.filter(BookDB.author.overlap(authors))

        # Фильтрация по году написания
        if year_from:
            query = query.filter(BookDB.year_of_create >= datetime(year_from, 1, 1))
        if year_to:
            query = query.filter(BookDB.year_of_create <= datetime(year_to, 12, 31))

        # Фильтрация по доступности для чтения
        if open_for_read is not None and user_id is not None:
            subquery = await self._get_open_for_read_subquery(user_id)
            query = query.filter(BookDB.id.in_(subquery))

        # Получаем общее количество книг
        total_query = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = total_query.scalar()

        # Применяем пагинацию
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        books = result.unique().scalars().all()

        return total, books

    async def _get_open_for_read_subquery(self, user_id: int):
        """
        Возвращает подзапрос для получения ID книг, доступных для чтения пользователем.

        :param user_id: ID пользователя.
        :return: Подзапрос с ID книг.
        """
        from src.db.models.transaction_models import UserTransactionDB, TransactionStatus

        # Книги, которые можно читать бесплатно
        free_books = select(BookDB.id).where(BookDB.prices.has(BookPriceDB.price == 0))

        # Книги, купленные пользователем
        bought_books = (
            select(UserTransactionDB.book_id)
            .where(
                UserTransactionDB.user_id == user_id,
                UserTransactionDB.status == TransactionStatus.BUY
            )
        )

        # Книги, взятые в аренду и срок аренды не истек
        rented_books = (
            select(UserTransactionDB.book_id)
            .where(
                UserTransactionDB.user_id == user_id,
                UserTransactionDB.status.in_([
                    TransactionStatus.RENT_2WEEK,
                    TransactionStatus.RENT_MONTH,
                    TransactionStatus.RENT_3MONTH
                ]),
                UserTransactionDB.date_buy + self._get_rent_duration(UserTransactionDB.status) > datetime.now()
            )
        )

        # Объединяем все подзапросы
        subquery = free_books.union(bought_books).union(rented_books)
        return subquery

    @staticmethod
    def _get_rent_duration(status):
        """
        Возвращает продолжительность аренды в зависимости от статуса транзакции.

        :param status: Статус транзакции.
        :return: Продолжительность аренды.
        """
        if status == TransactionStatus.RENT_2WEEK:
            return timedelta(weeks=2)
        elif status == TransactionStatus.RENT_MONTH:
            return timedelta(days=30)
        elif status == TransactionStatus.RENT_3MONTH:
            return timedelta(days=90)
        return timedelta(0)