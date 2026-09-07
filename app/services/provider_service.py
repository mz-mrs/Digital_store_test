import logging

from app.repositories import ProviderKeyRepository
from app.schemas.provider import ProviderIssueRequest
from provider.provider_simulator import provider_a, provider_b
from provider.provider_simulator import ProviderError

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(self, provider_key_repository: ProviderKeyRepository) -> None:
        self.provider_key_repository = provider_key_repository

    async def issue(
        self,
        issue_request: ProviderIssueRequest,
    ) -> tuple[str, str]:

        for provider in (provider_a, provider_b):
            try:
                response = await provider.issue(
                    issue_request=issue_request,
                    provider_key_repository=self.provider_key_repository,
                )

                if response.status == "ok":
                    return provider.name, response.code

                if response.status == "error":
                    logger.warning(
                        "Провайдер %s вернул ошибку: %s",
                        provider.name,
                        response.reason,
                    )

                    if response.reason == "out_of_stock":
                        continue


            except (ProviderError, TimeoutError) as exc:
                logger.warning(
                    "Провайдер %s request_id=%s неудача: %s ",
                    provider.name,
                    issue_request.request_id,
                    exc,
                )

        raise ProviderError(
            "Все провайдеры не смогли выдать товар"
        )