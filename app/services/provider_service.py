import logging

from app.clients import ProviderClient, ProviderError
from app.schemas.provider import ProviderIssueRequest

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(
            self,
            providers: tuple[ProviderClient, ...],
    ) -> None:
        self.providers = providers

    async def issue(
        self,
        issue_request: ProviderIssueRequest,
    ) -> tuple[str, str]:

        for provider in self.providers:
            try:
                response = await provider.issue(
                    issue_request=issue_request
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