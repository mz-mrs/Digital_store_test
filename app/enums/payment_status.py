from enum import Enum


class PaymentStatus(str, Enum):
    PAID = "paid"
    FAILED = "failed"