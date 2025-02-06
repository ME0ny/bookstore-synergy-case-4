from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.user_models import UserDB, UserWalletDB
from src.db.models.transaction_models import TransactionStatus, UserTransaction, UserTransactionDB
from datetime import datetime, timedelta

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_yandex_id(self, yandex_id: str):
        """Получить пользователя по Yandex ID."""
        result = await self.db.execute(select(UserDB).where(UserDB.yandex_id == yandex_id))
        return result.scalars().first()

    async def create_user(self, user: UserDB):
        """Создать нового пользователя."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user: UserDB):
        await self.db.commit()
        await self.db.refresh(user)
        return user
        
    async def create_user_wallet(self, user_id: int):
        """Создать кошелек для нового пользователя."""
        wallet = UserWalletDB(user_id=user_id)
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def get_user_wallet(self, user_id: int):
        """Получить кошелек пользователя."""
        result = await self.db.execute(select(UserWalletDB).where(UserWalletDB.user_id == user_id))
        return result.scalars().first()
    
    async def get_active_user_transaction(self, user_id: int, book_id: int):
        """
        Получить активную транзакцию пользователя для книги.
        
        :param user_id: ID пользователя
        :param book_id: ID книги
        :return: Активная транзакция (покупка или действующая аренда) или None, если активной транзакции нет.
        """
        result = await self.db.execute(
            select(UserTransactionDB).where(
                UserTransactionDB.user_id == user_id,
                UserTransactionDB.book_id == book_id
            )
        )
        transactions = result.scalars().all()

        for transaction in transactions:
            # Если книга куплена навсегда, возвращаем транзакцию
            if transaction.status == TransactionStatus.BUY:
                return transaction
            
            # Если книга арендована, проверяем срок аренды
            if transaction.status in [TransactionStatus.RENT_2WEEK, TransactionStatus.RENT_MONTH, TransactionStatus.RENT_3MONTH]:
                # Вычисляем срок окончания аренды
                if transaction.status == TransactionStatus.RENT_2WEEK:
                    rent_duration = timedelta(weeks=2)
                elif transaction.status == TransactionStatus.RENT_MONTH:
                    rent_duration = timedelta(days=30)
                elif transaction.status == TransactionStatus.RENT_3MONTH:
                    rent_duration = timedelta(days=90)
                
                # Проверяем, не истек ли срок аренды
                if datetime.now() < transaction.date_buy + rent_duration:
                    return transaction
        
        # Если активных транзакций нет, возвращаем None
        return None
    
    async def create_transaction(self, transaction: UserTransaction):
        """Создать транзакцию."""
        print(transaction)
        db_transaction = UserTransactionDB(**transaction.dict())
        print(db_transaction)
        self.db.add(db_transaction)
        await self.db.commit()
        await self.db.refresh(db_transaction)
        return db_transaction
    
    async def update_user_wallet(self, wallet: UserWalletDB):
        """Обновить баланс пользователя."""
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def get_all_user_transactions_for_book(self, user_id: int, book_id: int):
        """
        Возвращает все транзакции пользователя для данной книги.

        :param user_id: ID пользователя.
        :param book_id: ID книги.
        :return: Список всех транзакций.
        """
        result = await self.db.execute(
            select(UserTransactionDB).where(
                UserTransactionDB.user_id == user_id,
                UserTransactionDB.book_id == book_id
            )
        )
        return result.scalars().all()