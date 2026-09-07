from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import ProviderKeyRepository
from app.schemas.provider import (
    ProviderIssueRequest,
    ProviderIssueResponse,
)
from provider.provider_simulator import ProviderSimulator



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

        repository = ProviderKeyRepository(session)

        try:
            return await provider.issue(
                provider_key_repository=repository,
                issue_request=payload,
            )
        except TimeoutError:
            return ProviderIssueResponse(
                status="error",
                reason="timeout",
            )

    return router