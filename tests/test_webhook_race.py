import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from app.db.session import async_session_factory
from app.enums import DeliveryStatus
from app.models import Delivery, PaymentEvent


BASE_URL = "http://localhost:8000"

async def wait_for_delivery(
    order_id: str,
    timeout: float = 10.0,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout

    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=10.0,
    ) as client:
        while asyncio.get_running_loop().time() < deadline:
            response = await client.get(f"/orders/{order_id}")

            if response.status_code == 200:
                order = response.json()

                if order["status"] == "delivered":
                    return

            await asyncio.sleep(0.1)

    raise AssertionError(
        f"Заказ {order_id} не стал delivered за {timeout} секунд"
    )


@pytest.mark.asyncio
async def test_parallel_payment_webhooks_create_one_delivery(cleanup_orders):

    order_id = cleanup_orders(f"test-{uuid4()}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Создаём заказ
        response = await client.post(
            "/orders",
            json={
                "order_id": order_id,
                "sku": "STEAM-TOPUP-500",
                "quantity": 1,
            },
        )

        assert response.status_code == 201, response.text

        order = response.json()

        assert order["id"] == order_id
        assert order["status"] == "created"

        amount = order["amount"]
        currency = order["currency"]

        # 2. Формируем 10 разных webhook для одного заказа
        async def send_webhook():
            return await client.post(
                "/webhook/payment",
                json={
                    "event_id": str(uuid4()),
                    "order_id": order_id,
                    "status": "paid",
                    "amount": amount,
                    "currency": currency,
                    "created_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
            )

        # 3. Отправляем их одновременно
        responses = await asyncio.gather(
            *(send_webhook() for _ in range(10))
        )

        # Все webhook должны быть приняты
        assert all(
            response.status_code == 200
            for response in responses
        ), [
            response.text
            for response in responses
            if response.status_code != 200
        ]

    await wait_for_delivery(order_id)

    # 4. Проверяем результат в БД
    async with async_session_factory() as session:
        payment_events = (
            await session.scalars(
                select(PaymentEvent).where(
                    PaymentEvent.order_id == order_id
                )
            )
        ).all()

        deliveries = (
            await session.scalars(
                select(Delivery).where(
                    Delivery.order_id == order_id
                )
            )
        ).all()

        # Все 10 платежных событий сохранились
        assert len(payment_events) == 10

        # Но Delivery должна быть только одна
        assert len(deliveries) == 1

        delivery = deliveries[0]

        # Consumer должен в итоге выдать товар
        assert delivery.status == DeliveryStatus.DELIVERED
        assert delivery.code is not None


@pytest.mark.asyncio
async def test_duplicate_payment_webhooks_are_idempotent(cleanup_orders):
    order_id = cleanup_orders(f"test-duplicate-{uuid4()}")
    event_id = str(uuid4())

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.post(
            "/orders",
            json={
                "order_id": order_id,
                "sku": "STEAM-TOPUP-500",
                "quantity": 1,
            },
        )
        assert response.status_code == 201, response.text

        order = response.json()

        payload = {
            "event_id": event_id,
            "order_id": order_id,
            "status": "paid",
            "amount": order["amount"],
            "currency": order["currency"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await client.post(
            "/webhook/payment",
            json=payload,
        )
        assert response.status_code == 200, response.text

    await wait_for_delivery(order_id)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for _ in range(10):
            response = await client.post(
                "/webhook/payment",
                json=payload,
            )
            assert response.status_code == 200, response.text

    async with async_session_factory() as session:
        payment_events = (
            await session.scalars(
                select(PaymentEvent).where(
                    PaymentEvent.order_id == order_id
                )
            )
        ).all()

        deliveries = (
            await session.scalars(
                select(Delivery).where(
                    Delivery.order_id == order_id
                )
            )
        ).all()

        assert len(payment_events) == 1
        assert payment_events[0].event_id == event_id

        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.DELIVERED
        assert deliveries[0].code is not None