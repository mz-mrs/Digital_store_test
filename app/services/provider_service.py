import logging

from app.clients import ProviderClient, ProviderError
from app.schemas.provider import ProviderIssueRequest

logger = logging.getLogger(__name__)


class ProviderOutOfStockError(ProviderError):
    pass


class ProviderDeliveryError(ProviderError):
    pass


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

        out_of_stock_error = True

        for provider in self.providers:
            try:
                response = await provider.issue(
                    issue_request=issue_request
                )

                if response.status == "ok":
                    return provider.name, response.code

                if response.reason != "out_of_stock":
                    out_of_stock_error = False


            except (ProviderError, TimeoutError) as exc:

                out_of_stock_error = False

                logger.warning(
                    "Провайдер %s request_id=%s неудача: %s ",
                    provider.name,
                    issue_request.request_id,
                    exc,
                )

        if out_of_stock_error:
            raise ProviderOutOfStockError(
                "Все провайдеры сообщили об отсутствии выдачи"
            )

        raise ProviderDeliveryError(
            "Все провайдеры не смогли осуществить выдачу"
        )