from enum import Enum


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    OUT_OF_STOCK = "out_of_stock"
    FAILED = "failed"