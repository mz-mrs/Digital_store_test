import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.publisher import DeliveryPublisher
from app.clients import ProviderError
from app.core.generate_ids import generate_request_id
from app.enums import OrderStatus, PaymentStatus, DeliveryStatus
from app.models import Delivery
from app.repositories import PaymentRepository
from app.schemas.payment import PaymentWebhook
from app.schemas.provider import ProviderIssueRequest
from app.services.provider_service import ProviderService, ProviderOutOfStockError, ProviderDeliveryError

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(
            self,
            session: AsyncSession,
            provider_service: ProviderService,
            publisher: DeliveryPublisher | None = None,
    ) -> None:
        self.session = session
        self.repository = PaymentRepository(session)
        self.provider_service = provider_service
        self.publisher = publisher

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

            await self.publisher.publish(delivery.id)

            logger.info(
                "Задача на выдачу отправлена в очередь "
                "order_id=%s delivery_id=%s request_id=%s",
                order.id,
                delivery.id,
                delivery.request_id,
            )

            # issue_request = ProviderIssueRequest(
            #     request_id=delivery.request_id,
            #     sku=delivery.sku,
            #     order_id=delivery.order_id,
            # )
            #
            # try:
            #
            #     provider, code = await self.provider_service.issue(
            #         issue_request=issue_request,
            #     )
            #
            # except ProviderError as exc:
            #     logger.error(
            #         "Не удалось выдать товар order_id=%s request_id=%s error=%s",
            #         order.id,
            #         delivery.request_id,
            #         exc,
            #     )
            #
            #     delivery.status = DeliveryStatus.PENDING
            #     await self.session.commit()
            #     return
            #
            # delivery.provider = provider
            # delivery.code = code
            # delivery.status = DeliveryStatus.DELIVERED
            #
            # # provider_key = await self.provider_key_repository.take_available_key(
            # #     delivery_id=delivery.id,
            # #     request_id=request_id
            # # )
            # #
            # # if provider_key is None:
            # #     logger.error(
            # #         "Нет доступных ключей для доставки order_id=%s",
            # #         order.id,
            # #     )
            # #
            # #     await self.session.rollback()
            # #     return
            #
            # logger.info(
            #     "Товар выдан order_id=%s provider=%s request_id=%s",
            #     order.id,
            #     provider,
            #     delivery.request_id
            # )

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

    async def process_delivery(
            self,
            delivery_id: int,
    ) -> None:

        delivery = await self.repository.get_delivery_for_update(
            delivery_id
        )

        if delivery is None:
            logger.error(
                "Не найдена delivery_id=%s",
                delivery_id,
            )
            await self.session.rollback()
            return

        if delivery.status not in (
                DeliveryStatus.PENDING,
                DeliveryStatus.FAILED,
                DeliveryStatus.OUT_OF_STOCK,
        ):
            logger.info(
                "Не требует обработки delivery_id=%s status=%s",
                delivery.id,
                delivery.status.value,
            )
            await self.session.rollback()
            return

        order = await self.repository.get_order_for_update(
            delivery.order_id
        )

        if order is None:
            logger.error(
                "Не найден order_id=%s для delivery_id=%s",
                delivery.order_id,
                delivery.id,
            )
            await self.session.rollback()
            return

        delivery.status = DeliveryStatus.DELIVERING
        order.status = OrderStatus.DELIVERING


        await self.session.commit()

        logger.info(
            "Идет получение кода у поставщика order_id=%s delivery_id=%s request_id=%s",
            delivery.order_id,
            delivery.id,
            delivery.request_id,
        )


        issue_request = ProviderIssueRequest(
            request_id=delivery.request_id,
            sku=delivery.sku,
            order_id=delivery.order_id,
        )

        try:
            provider, code = await self.provider_service.issue(
                issue_request=issue_request,
            )

        except ProviderOutOfStockError:

            delivery.status = DeliveryStatus.OUT_OF_STOCK
            order.status = OrderStatus.OUT_OF_STOCK

            await self.session.commit()

            logger.warning(
                "Товар закончился у всех провайдеров order_id=%s delivery_id=%s request_id=%s",
                delivery.order_id,
                delivery.id,
                delivery.request_id,
            )
            return

        except ProviderDeliveryError:

            delivery.status = DeliveryStatus.FAILED
            order.status = OrderStatus.DELIVERY_FAILED

            await self.session.commit()

            logger.exception(
                "Не удалось осуществить выдачу order_id=%s delivery_id=%s request_id=%s",
                delivery.order_id,
                delivery.id,
                delivery.request_id,
            )
            raise


        delivery.provider = provider
        delivery.code = code
        delivery.status = DeliveryStatus.DELIVERED
        order.status = OrderStatus.DELIVERED

        await self.session.commit()

        logger.info(
            "Код выдан и привязан к заказу order_id=%s provider=%s delivery_id=%s request_id=%s",
            delivery.order_id,
            provider,
            delivery.id,
            delivery.request_id,
        )

