from app.enums import OrderStatus
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
            "Процесс создания заказа запущен: sku=%s quantity=%s",
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

        logger.info(
            "Заказ создан успешно: order_id=%s amount=%s",
            order.id,
            amount,
        )

        return await self.repository.create(order)