import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from simulators.provider.provider_key_repository import ProviderKeyRepository
from app.schemas.provider import (
    ProviderIssueRequest,
    ProviderIssueResponse,
)
from simulators.provider.provider_simulator import ProviderSimulator

logger = logging.getLogger(__name__)


def create_provider_router(provider: ProviderSimulator) -> APIRouter:

    router = APIRouter(
        tags=["provider"],
    )

    @router.post(
        "/issue",
        response_model=ProviderIssueResponse,
        response_model_exclude_none=True,
    )
    async def issue(
        payload: ProviderIssueRequest,
        session: AsyncSession = Depends(get_session),
    ) -> ProviderIssueResponse:

        logger.info(
            "Получен запрос на выдачу: provider=%s request_id=%s order_id=%s sku=%s",
            provider.name,
            payload.request_id,
            payload.order_id,
            payload.sku,
        )

        repository = ProviderKeyRepository(session)

        try:
            response =  await provider.issue(
                provider_key_repository=repository,
                issue_request=payload,
            )

            logger.info(
                "Запрос обработан: provider=%s request_id=%s status=%s code=%s reason=%s",
                provider.name,
                response.request_id,
                response.status,
                response.code,
                response.reason,
            )

            return response

        except TimeoutError:

            logger.warning(
                "Таймаут провайдера: provider=%s request_id=%s order_id=%s",
                provider.name,
                payload.request_id,
                payload.order_id,
            )

            return ProviderIssueResponse(
                status="error",
                reason="timeout",
            )

    return router