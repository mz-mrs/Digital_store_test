from app.enums import OrderStatus
from app.models import Order, OrderItem
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate


class ProductNotFoundError(Exception):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def create_order(self, data: OrderCreate) -> Order:
        product = await self.repository.get_product_by_sku(data.sku)

        if product is None:
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

        return await self.repository.create(order)