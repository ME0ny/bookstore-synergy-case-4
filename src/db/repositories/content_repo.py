from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.book_models import BookContentDB

class ContentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_content(self, book_id: int, url_content: str):
        result = await self.db.execute(select(BookContentDB).where(BookContentDB.book_id == book_id))
        db_content = result.scalars().first()
        if not db_content:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        # Устанавливаем hidden в True
        db_content.url_content = url_content
        await self.db.commit()
        await self.db.refresh(db_content)
        return db_content

    async def get_content_by_book_id(self, book_id: int):
        result = await self.db.execute(select(BookContentDB).where(BookContentDB.book_id == book_id))
        return result.scalars().first()