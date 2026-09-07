from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_payment_service
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
    service: PaymentService = Depends(get_payment_service),
) -> PaymentWebhookResponse:

    await service.process_webhook(payload)

    return PaymentWebhookResponse()