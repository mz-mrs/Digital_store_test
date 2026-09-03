import asyncio
import json
import logging
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.product import Currency, Product, ProductType

logger = logging.getLogger(__name__)


PRODUCTS_FILE = Path(__file__).parent.parent / "data" / "catalog.json"


async def products_to_db() -> None:
    with PRODUCTS_FILE.open(encoding="utf-8") as file:
        products_data = json.load(file)

    async with async_session_factory() as session:
        for data in products_data:
            result = await session.execute(
                select(Product).where(Product.sku == data["sku"])
            )
            product = result.scalar_one_or_none()

            if product is not None:
                continue

            product = Product(
                sku=data["sku"],
                name=data["name"],
                type=ProductType(data["type"]),
                price=Decimal(data["price"]),
                currency=Currency(data["currency"]),
                image=data["image"],
            )
            session.add(product)

        await session.commit()

        logger.info("Успешная загрузка товаров в базу")


if __name__ == "__main__":
    asyncio.run(products_to_db())