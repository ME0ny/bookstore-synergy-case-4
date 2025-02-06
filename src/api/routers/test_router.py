from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from src.db.session import get_db

router = APIRouter()

@router.get("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    try:
        # Выполняем простой SQL-запрос
        result = await db.execute(text("SELECT version()"))
        version = result.scalar()
        return {"database_version": version}
    except Exception as e:
        return {"error": str(e)}
