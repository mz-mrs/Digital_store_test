from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies import get_order_service, get_order_repository
from app.repositories.order import OrderRepository
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
    description='Создание заказа'
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


@router.get(
    "/{id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    description='Получение заказа по id'
)
async def get_order(
    id: UUID,
    repository: OrderRepository = Depends(get_order_repository),
) -> OrderResponse:

    order = await repository.get_by_id(id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ {id=} не найден",
        )

    return OrderResponse.model_validate(order)