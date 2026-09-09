from fastapi import APIRouter

from app.enums import PaymentStatus
from simulators.payment.payment_simulator import PaymentSimulator


def create_payment_router(
    simulator: PaymentSimulator,
) -> APIRouter:
    router = APIRouter(
        prefix="/payment",
        tags=["payment-simulator"],
    )

    @router.post("/pay/{order_id}")
    async def pay(
            order_id: str,
            status: PaymentStatus
    ) -> dict[str, str]:

        await simulator.send_webhook(
            order_id=order_id,
            status=status
        )

        return {
            "status": status,
            "order_id": order_id,
        }

    return router