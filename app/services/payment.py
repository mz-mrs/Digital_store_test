import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import ProviderError
from app.core.generate_ids import generate_request_id
from app.enums import OrderStatus, PaymentStatus, DeliveryStatus
from app.models import Delivery
from app.repositories import PaymentRepository
from app.schemas.payment import PaymentWebhook
from app.schemas.provider import ProviderIssueRequest
from app.services.provider_service import ProviderService

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(
            self,
            session: AsyncSession,
            provider_service: ProviderService
    ) -> None:
        self.session = session
        self.repository = PaymentRepository(session)
        self.provider_service = provider_service

    async def process_webhook(
        self,
        payload: PaymentWebhook,
    ) -> None:

        logger.info(
            "Получен вебхук event_id=%s order_id=%s status=%s",
            payload.event_id,
            payload.order_id,
            payload.status.value
        )

        order = await self.repository.get_order_for_update(
            payload.order_id
        )

        created_payment_event = await self.repository.create_payment_event(payload)


        if not created_payment_event:
            logger.info(
                "Вебхук повторный, игнор order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id
            )
            await self.session.rollback()
            return

        if order is None:
            logger.info(
                "Заказ еще не создан, вебхук сохранен order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id,
            )
            await self.session.commit()
            return

        logger.info(
            "Вебхук оплаты прошел проверку успешно event_id=%s order_id=%s status=%s",
            payload.event_id,
            payload.order_id,
            payload.status.value
        )

        if order.status != OrderStatus.CREATED:

            await self.session.commit()
            logger.info(
                "Невозможно обработать вебхук event_id=%s order_id=%s, статус заказа %s",
                payload.event_id,
                payload.order_id,
                order.status.value
            )
            return

        if payload.status == PaymentStatus.PAID:
            order.status = OrderStatus.PAID

            request_id=generate_request_id(order.id, 1)

            delivery = Delivery(
                order_id=order.id,
                request_id=request_id,
                sku=order.items[0].sku,
                status=DeliveryStatus.PENDING,
            )

            self.session.add(delivery)
            await self.session.flush()

            await self.session.commit()


            issue_request = ProviderIssueRequest(
                request_id=delivery.request_id,
                sku=delivery.sku,
                order_id=delivery.order_id,
            )

            try:

                provider, code = await self.provider_service.issue(
                    issue_request=issue_request,
                )

            except ProviderError as exc:
                logger.error(
                    "Не удалось выдать товар order_id=%s request_id=%s error=%s",
                    order.id,
                    delivery.request_id,
                    exc,
                )

                delivery.status = DeliveryStatus.PENDING
                await self.session.commit()
                return

            delivery.provider = provider
            delivery.code = code
            delivery.status = DeliveryStatus.DELIVERED

            # provider_key = await self.provider_key_repository.take_available_key(
            #     delivery_id=delivery.id,
            #     request_id=request_id
            # )
            #
            # if provider_key is None:
            #     logger.error(
            #         "Нет доступных ключей для доставки order_id=%s",
            #         order.id,
            #     )
            #
            #     await self.session.rollback()
            #     return

            logger.info(
                "Товар выдан order_id=%s provider=%s request_id=%s",
                order.id,
                provider,
                delivery.request_id
            )

        else:
            order.status = OrderStatus.PAYMENT_FAILED

            logger.info(
                "Статус заказа не оплачен order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id
            )

        await self.session.commit()

        logger.info(
            "Вебхук обработан event_id=%s order_id=%s status=%s",
            payload.event_id,
            payload.order_id,
            order.status
        )

