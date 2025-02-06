from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.book_models import BookPrice, Book, BookPriceDB, BookWithPrice, BookDB, BookContentDB, PaginatedBooksResponse
from src.db.models.user_models import UserWalletDB, UserDB
from src.db.models.feed_models import FeedBook, FeedBookStatus
from src.db.models.transaction_models import TransactionStatus, UserTransaction, UserTransactionDB
from src.db.repositories.book_repo import BookRepository
from src.db.repositories.user_repo import UserRepository
from src.db.repositories.content_repo import ContentRepository
from src.db.session import get_db
import os
from PyPDF2 import PdfReader
from ebooklib import epub
from ebooklib import ITEM_DOCUMENT
from typing import List, Tuple, Optional

class BookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.book_repo = BookRepository(db)
        self.user_repo = UserRepository(db)
        self.content_repo = ContentRepository(db)
    
    async def update_book(self, book_id: int, updated_data: dict):
        """
        Обновляет информацию о книге.

        :param book_id: ID книги.
        :param updated_data: Словарь с новыми данными для обновления.
        :return: Обновленную книгу или ошибку.
        """
        return await self.book_repo.update_book(book_id, updated_data)

    async def get_book_page(self, user: UserDB, book_id: int, page: int):
        """
        Получить страницу книги с проверкой доступа.
        
        :param user: Текущий пользователь.
        :param book_id: ID книги.
        :param page: Номер страницы.
        :return: Содержимое страницы или ошибка.
        """
        # Проверяем права доступа к книге
        if not await self.is_book_accessible(user.id, book_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав на чтение этой книги.")
        
        # Получаем содержимое книги
        content = await self.content_repo.get_content_by_book_id(book_id)
        if not content or not content.url_content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Содержимое книги не найдено.")
        
        # Читаем страницу из файла
        try:
            file_extension = os.path.splitext(content.url_content)[1].lower()
            if file_extension == ".pdf":
                text = await self._read_pdf_page(content.url_content, page)
            elif file_extension == ".epub":
                text = await self._read_epub_page(content.url_content, page)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неподдерживаемый формат файла.")
            
            return {"page": page, "content": text}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка при чтении книги: {str(e)}")

    async def is_book_accessible(self, user_id: int, book_id: int) -> bool:
        """
        Проверяет, имеет ли пользователь доступ к книге.
        
        :param user_id: ID пользователя.
        :param book_id: ID книги.
        :return: True, если доступ есть, иначе False.
        """
        # Проверяем, существует ли книга
        book = await self.book_repo.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена.")

        # Проверяем, является ли книга бесплатной
        book_price = await self.book_repo.get_book_price_by_id(book_id)
        if book_price and book_price.price == 0 and book.hidden == False:
            return True

        # Проверяем транзакции пользователя
        active_transaction = await self.user_repo.get_active_user_transaction(user_id, book_id)
        if active_transaction:
            if active_transaction.status == TransactionStatus.BUY:
                return True
            elif active_transaction.status in [
                TransactionStatus.RENT_2WEEK,
                TransactionStatus.RENT_MONTH,
                TransactionStatus.RENT_3MONTH,
            ]:
                # Проверяем срок аренды
                now = datetime.now()
                if active_transaction.status == TransactionStatus.RENT_2WEEK:
                    expiration_date = active_transaction.date_buy + timedelta(weeks=2)
                elif active_transaction.status == TransactionStatus.RENT_MONTH:
                    expiration_date = active_transaction.date_buy + timedelta(days=30)
                elif active_transaction.status == TransactionStatus.RENT_3MONTH:
                    expiration_date = active_transaction.date_buy + timedelta(days=90)
                
                return now < expiration_date
        
        return False

    async def get_all_books_with_prices(self) -> List[BookWithPrice]:
        """
        Возвращает список всех книг вместе с их ценами.

        :return: Список объектов BookWithPrice.
        """
        books_with_prices = await self.book_repo.get_all_books_with_prices()
        result = []

        for book_db, price_db in books_with_prices:
            book_data = {
                "id": book_db.id,
                "title": book_db.title,
                "url_img": book_db.url_img,
                "category": book_db.category,
                "author": book_db.author,
                "year_of_create": book_db.year_of_create,
                "hidden": book_db.hidden,
            }
            result.append(BookWithPrice(
                book=book_data, 
                price=price_db.price, 
                price_rent_2week=price_db.price_rent_2week, 
                price_rent_month=price_db.price_rent_month, 
                price_rent_3month=price_db.price_rent_3month
                ))

        return result

    async def get_books_with_prices_paginated(
        self,
        page: int = 1,
        limit: int = 10
    ) -> PaginatedBooksResponse:
        """
        Возвращает книги с ценами с поддержкой пагинации.
        
        :param page: Номер страницы.
        :param limit: Количество элементов на странице.
        :return: Ответ с пагинированным списком книг.
        """
        total, books = await self.book_repo.get_books_with_prices_paginated(page, limit)

        # Преобразуем результаты в список объектов BookWithPrice
        book_list = []
        for book in books:
            price_db = getattr(book, "prices", None)  # Получаем связанные цены, если они есть
            book_data = {
                "id": book.id,
                "title": book.title,
                "url_img": book.url_img,
                "category": book.category,
                "author": book.author,
                "year_of_create": book.year_of_create,
                "hidden": book.hidden,
            }
            book_list.append(BookWithPrice(
                book=book_data, 
                price=price_db.price, 
                price_rent_2week=price_db.price_rent_2week, 
                price_rent_month=price_db.price_rent_month, 
                price_rent_3month=price_db.price_rent_3month
                ))
        print(total, type(total))
        return PaginatedBooksResponse(
            total=total,
            page=page,
            limit=limit,
            books=book_list
        )

    async def get_filtered_feed_books(
        self,
        user: UserDB,
        categories: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        open_for_read: Optional[bool] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[int, List[FeedBook]]:
        """
        Возвращает отфильтрованную ленту книг для пользователя.

        :param user: Текущий пользователь.
        :param categories: Список категорий для фильтрации.
        :param authors: Список авторов для фильтрации.
        :param year_from: Минимальный год написания.
        :param year_to: Максимальный год написания.
        :param open_for_read: Фильтр по доступности для чтения.
        :param page: Номер страницы.
        :param limit: Количество элементов на странице.
        :return: Общее количество книг и список книг.
        """
        total, books = await self.book_repo.get_filtered_books(
            categories=categories,
            authors=authors,
            year_from=year_from,
            year_to=year_to,
            open_for_read=open_for_read,
            user_id=user.id,
            page=page,
            limit=limit
        )

        feed_books = []
        for book in books:
            price_db = getattr(book, "prices", None)
            price_data = {
                "book_id": price_db.book_id if price_db else None,
                "price": price_db.price if price_db else None,
                "price_rent_2week": price_db.price_rent_2week if price_db else None,
                "price_rent_month": price_db.price_rent_month if price_db else None,
                "price_rent_3month": price_db.price_rent_3month if price_db else None,
            }

            # Определяем статус книги
            status = await self._get_book_status(user.id, book.id)
            print(status)
            feed_books.append(FeedBook(
                book=Book(**book.__dict__),
                price=BookPrice(**price_data),
                open_for_read=status in [
                    FeedBookStatus.BUY,
                    FeedBookStatus.RENT_2WEEK,
                    FeedBookStatus.RENT_MONTH,
                    FeedBookStatus.RENT_3MONTH
                ],
                status=status
            ))

        return total, feed_books

    async def _get_book_status(self, user_id: int, book_id: int) -> Optional[str]:
        """
        Определяет статус книги для пользователя.

        :param user_id: ID пользователя.
        :param book_id: ID книги.
        :return: Статус книги (FeedBookStatus) или None, если книга платная и не взаимодействована.
        """
        # 1. Проверяем, является ли книга бесплатной
        book_price = await self.book_repo.get_book_price_by_id(book_id)
        if book_price and book_price.price == 0:
            return FeedBookStatus.READ_FREE

        # 2. Проверяем транзакции пользователя для данной книги
        active_transaction = await self.user_repo.get_active_user_transaction(user_id, book_id)
        if active_transaction:
            if active_transaction.status == TransactionStatus.BUY:
                return FeedBookStatus.BUY

            elif active_transaction.status in [
                TransactionStatus.RENT_2WEEK,
                TransactionStatus.RENT_MONTH,
                TransactionStatus.RENT_3MONTH,
            ]:
                # Рассчитываем дату окончания аренды
                expiration_date = self._calculate_expiration_date(
                    active_transaction.status, active_transaction.date_buy
                )

                if datetime.now() < expiration_date:
                    # Аренда еще действует
                    return active_transaction.status  # Возвращаем строковое значение статуса
                else:
                    # Срок аренды истек
                    return FeedBookStatus.RENT_END

        # 3. Если книга платная и нет активных транзакций, возвращаем None
        return None

    @staticmethod
    def _calculate_expiration_date(status: str, date_buy: datetime) -> datetime:
        """
        Вычисляет дату окончания аренды.

        :param status: Статус транзакции.
        :param date_buy: Дата покупки/аренды.
        :return: Дата окончания аренды.
        """
        if status == TransactionStatus.RENT_2WEEK:
            return date_buy + timedelta(weeks=2)
        elif status == TransactionStatus.RENT_MONTH:
            return date_buy + timedelta(days=30)
        elif status == TransactionStatus.RENT_3MONTH:
            return date_buy + timedelta(days=90)
        return date_buy

    @staticmethod
    async def _read_pdf_page(file_path: str, page: int) -> str:
        """Чтение страницы PDF."""
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        if page < 0 or page >= len(reader.pages):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый номер страницы.")
        return reader.pages[page].extract_text()

    @staticmethod
    async def _read_epub_page(file_path: str, page: int) -> str:
        """Чтение страницы EPUB."""
        from ebooklib import epub
        book = epub.read_epub(file_path)
        items = list(book.get_items_of_type(ITEM_DOCUMENT))
        print(file_path)
        print(items)
        print(len(items), page)
        if page < 0 or page >= len(items):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый номер страницы.")
        return items[page].get_body_content().decode("utf-8")

    async def purchase_or_rent_book(self, user_id: int, book_id: int, action: str):
        """
        Покупка или аренда книги.
        
        :param user_id: ID пользователя
        :param book_id: ID книги
        :param action: Действие (покупка или аренда)
        :return: Результат операции
        """
        # Получаем информацию о книге и ее цене
        book = await self.book_repo.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена")

        # Проверяем, скрыта ли книга
        if book.hidden:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Книга скрыта и недоступна для покупки/аренды")

        # Получаем цену книги
        book_price = await self.book_repo.get_book_price_by_id(book_id)
        if not book_price:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Цена книги не найдена")

        # Определяем стоимость в зависимости от действия
        if action == "buy":
            price = book_price.price
            transaction_status = TransactionStatus.BUY
        elif action == "rent_2week":
            price = book_price.price_rent_2week
            transaction_status = TransactionStatus.RENT_2WEEK
        elif action == "rent_month":
            price = book_price.price_rent_month
            transaction_status = TransactionStatus.RENT_MONTH
        elif action == "rent_3month":
            price = book_price.price_rent_3month
            transaction_status = TransactionStatus.RENT_3MONTH
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверное действие")

        # Проверяем, что цена не равна 0
        if price == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Книга недоступна для покупки/аренды")

        # Получаем баланс пользователя
        user_wallet = await self.user_repo.get_user_wallet(user_id)
        if not user_wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Кошелек пользователя не найден")

        # Проверяем, хватает ли средств у пользователя
        if user_wallet.account < price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно средств на балансе")

        # Проверяем, не купил ли пользователь уже эту книгу
        existing_transaction = await self.user_repo.get_active_user_transaction(user_id, book_id)
        if existing_transaction:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Книга уже куплена/арендована")

        # Создаем транзакцию
        transaction = UserTransaction(
            user_id=user_id,
            book_id=book_id,
            date_buy=datetime.now(),
            price=price,
            status=transaction_status
        )

        # Обновляем баланс пользователя
        user_wallet.account -= price

        # Сохраняем транзакцию и обновляем баланс
        await self.user_repo.create_transaction(transaction)
        await self.user_repo.update_user_wallet(user_wallet)

        return {"message": "Книга успешно куплена/арендована", "transaction": transaction}