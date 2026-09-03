from app.enums import OrderStatus, PaymentStatus
from app.models import Order, OrderItem
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate

import logging

logger = logging.getLogger(__name__)


class ProductNotFoundError(Exception):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def create_order(self, data: OrderCreate) -> Order:

        logger.info(
            "Процесс создания заказа запущен: order_id=%s, sku=%s quantity=%s",
            data.order_id,
            data.sku,
            data.quantity,
        )

        product = await self.repository.get_product_by_sku(data.sku)

        if product is None:
            logger.warning("Товар не найден: sku=%s", data.sku)
            raise ProductNotFoundError(
                f"Товар '{data.sku}' не найден"
            )

        amount = product.price * data.quantity

        order = Order(
            id=data.order_id,
            status=OrderStatus.CREATED,
            amount=amount,
            currency=product.currency.value,
        )

        order.items.append(
            OrderItem(
                sku=product.sku,
                quantity=data.quantity,
                price=product.price,
            )
        )

        payment_event = await self.repository.get_payment_event(data.order_id)

        if payment_event is not None:
            if payment_event.status == PaymentStatus.PAID:
                order.status = OrderStatus.PAID
            else:
                order.status = OrderStatus.PAYMENT_FAILED

            logger.info(
                "Для нового заказа найден платежный вебхук: order_id=%s event_id=%s status=%s",
                data.order_id,
                payment_event.event_id,
                payment_event.status.value,
            )

        order = await self.repository.create(order)

        logger.info(
            "Заказ создан успешно: order_id=%s amount=%s",
            order.id,
            amount,
        )

        return order