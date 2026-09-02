from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductType(StrEnum):
    TOPUP = "topup"
    KEY = "key"
    SUBSCRIPTION = "subscription"
    GIFTCARD = "giftcard"


class Currency(StrEnum):
    RUB = "RUB"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    type: Mapped[ProductType] = mapped_column(
        Enum(
            ProductType,
            name="product_type",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency"),
        nullable=False,
    )

    image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
    )