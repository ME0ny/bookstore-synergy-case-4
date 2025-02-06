from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.services.book_service import BookService
from src.db.models.user_models import UserDB
from src.core.security import get_current_user
from src.db.models.transaction_models import TransactionStatus
from src.db.models.transaction_models import TransactionResponse

router = APIRouter(prefix="/purchase", tags=["purchase"])

@router.post("/{book_id}/{action}", response_model=TransactionResponse)
async def purchase_or_rent_book(
    book_id: int,
    action: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    book_service = BookService(db)
    result = await book_service.purchase_or_rent_book(current_user.id, book_id, action)
    return TransactionResponse(
        message=result["message"],
        transaction=result["transaction"].dict()
    )