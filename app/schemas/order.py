from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.enums import OrderStatus


class OrderCreate(BaseModel):
    order_id: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    quantity: int
    price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: OrderStatus
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]