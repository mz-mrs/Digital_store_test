from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies import get_order_service
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order import OrderService, ProductNotFoundError

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order = await service.create_order(data)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return OrderResponse.model_validate(order)