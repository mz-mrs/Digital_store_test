from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import DeliveryStatus


if TYPE_CHECKING:
    from app.models import Order


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    request_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    sku: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(
            DeliveryStatus,
            name="delivery_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=DeliveryStatus.PENDING,
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

    order: Mapped["Order"] = relationship(
        back_populates="delivery",
    )