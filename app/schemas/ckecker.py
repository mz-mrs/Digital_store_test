from pydantic import BaseModel


class CheckingItem(BaseModel):
    order_id: str
    delivery_id: str
    order_status: str
    delivery_status: str


class CheckingItemResponse(BaseModel):
    paid_not_delivered: list[CheckingItem]
    delivered_not_paid: list[CheckingItem]