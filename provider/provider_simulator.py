import asyncio
from random import random
from uuid import UUID

from app.repositories import ProviderKeyRepository
from app.schemas.provider import ProviderIssueRequest, ProviderIssueResponse


class ProviderError(Exception):
    pass

class ProviderSimulator:
    def __init__(
        self,
        name: str,
        error_chance: float = 0.1,
        timeout_chance: float = 0.1,
        timeout_delay: float = 5.0,
    ) -> None:
        if error_chance < 0 or timeout_chance < 0:
            raise ValueError("Вероятность ошибки должна быть >= 0")

        if error_chance + timeout_chance > 1:
            raise ValueError("Вероятность ошибки и таймаута должны быть <= 1")

        self.name = name
        self.error_chance = error_chance
        self.timeout_chance = timeout_chance
        self.timeout_delay = timeout_delay

    async def issue(
        self,
        provider_key_repository: ProviderKeyRepository,
        issue_request: ProviderIssueRequest,
    ) -> ProviderIssueResponse:

        existing_key = await provider_key_repository.get_by_request_id(
            issue_request.request_id
        )

        if existing_key is not None:
            return ProviderIssueResponse(
                status="ok",
                request_id=issue_request.request_id,
                code=existing_key.code,
            )

        roll = random()

        if roll < self.error_chance:
            raise ProviderError(
                f"Провайдер {self.name} вернул 500"
            )

        key = await provider_key_repository.take_available_key(
            request_id=issue_request.request_id,
            order_id=issue_request.order_id,
        )

        if key is None:
            return ProviderIssueResponse(
                status='error',
                reason='out_of_stock'
            )
            # raise ProviderError(
            #     f"Провайдер {self.name}: out of stock"
            # )

        if roll < self.error_chance + self.timeout_chance:
            await asyncio.sleep(self.timeout_delay)

            raise TimeoutError(
                f"Провайдер {self.name} таймаут"
            )

        return ProviderIssueResponse(
            status='ok',
            request_id=issue_request.request_id,
            code=key.code
        )



provider_a = ProviderSimulator(
    name="A",
    error_chance=0.1,
    timeout_chance=0.1,
)

provider_b = ProviderSimulator(
    name="B",
    error_chance=0.05,
    timeout_chance=0.05,
)