from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    PAYMENT_FAILED = "payment_failed"
    OUT_OF_STOCK = "out_of_stock"
    DELIVERY_FAILED = "delivery_failed"