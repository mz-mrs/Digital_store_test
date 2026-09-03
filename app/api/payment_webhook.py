from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.payment import PaymentWebhook, PaymentWebhookResponse
from app.services import PaymentService


router = APIRouter(
    prefix="/webhook",
    tags=["payment"],
)


@router.post(
    "/payment",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
)
async def payment_webhook(
    payload: PaymentWebhook,
    session: AsyncSession = Depends(get_session),
) -> PaymentWebhookResponse:
    service = PaymentService(session)

    await service.process_webhook(payload)

    return PaymentWebhookResponse()