from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import ProviderKeyStatus

if TYPE_CHECKING:
    from app.models import Delivery


class ProviderKey(Base):
    __tablename__ = "provider_keys"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[ProviderKeyStatus] = mapped_column(
        Enum(
            ProviderKeyStatus,
            name="provider_key_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ProviderKeyStatus.AVAILABLE,
        index=True,
    )

    delivery_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("deliveries.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    delivery: Mapped["Delivery | None"] = relationship(
        back_populates="provider_key",
    )