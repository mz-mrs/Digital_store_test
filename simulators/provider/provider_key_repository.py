from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ProviderKeyStatus
from app.models import Delivery, ProviderKey


class ProviderKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def take_available_key(
            self,
            request_id: str,
            order_id: str,
    ) -> ProviderKey | None:

        result = await self.session.execute(
            select(Delivery)
            .where(
                Delivery.order_id == order_id,
                Delivery.request_id == request_id,
            )
            .with_for_update()
        )

        delivery = result.scalar_one_or_none()

        if delivery is None:
            return None

        result = await self.session.execute(
            select(ProviderKey)
            .where(
                ProviderKey.delivery_id == delivery.id,
                ProviderKey.status == ProviderKeyStatus.ISSUED,
            )
        )

        existing_key = result.scalar_one_or_none()

        if existing_key is not None:
            return existing_key

        result = await self.session.execute(
            select(ProviderKey)
            .where(
                ProviderKey.status == ProviderKeyStatus.AVAILABLE
            )
            .order_by(ProviderKey.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        key = result.scalar_one_or_none()

        if key is None:
            return None

        key.status = ProviderKeyStatus.ISSUED
        key.delivery_id = delivery.id

        return key

    async def get_by_request_id(
            self,
            request_id: str,
    ) -> ProviderKey | None:

        result = await self.session.execute(
            select(ProviderKey)
            .join(
                Delivery,
                ProviderKey.delivery_id == Delivery.id,
            )
            .where(
                Delivery.request_id == request_id
            )
        )

        return result.scalar_one_or_none()