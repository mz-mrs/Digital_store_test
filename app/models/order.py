from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import OrderStatus

if TYPE_CHECKING:
    from app.models import Delivery, OrderItem

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=OrderStatus.CREATED,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    delivery: Mapped["Delivery | None"] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        uselist=False,
    )