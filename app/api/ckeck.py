from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.ckecker import CheckingItemResponse
from app.services import CheckService


router = APIRouter(
    prefix="/check",
    tags=["check"],
)


@router.get(
    "",
    response_model=CheckingItemResponse,
)
async def check(session: AsyncSession = Depends(get_session)) -> CheckingItemResponse:

    service = CheckService(session)

    return await service.check_items()