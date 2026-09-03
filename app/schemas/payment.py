from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.enums import PaymentStatus


class PaymentWebhook(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=255)
    order_id: str = Field(min_length=1, max_length=255)
    status: PaymentStatus
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    created_at: datetime

class PaymentWebhookResponse(BaseModel):
    status: str = "success"