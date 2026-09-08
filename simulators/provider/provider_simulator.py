import asyncio
import logging
from random import random

from simulators.provider.provider_key_repository import ProviderKeyRepository
from simulators.provider.provider_schemas import ProviderIssueRequest, ProviderIssueResponse


logger = logging.getLogger(__name__)

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
            logger.info(
                "Провайдер %s: повторный запрос, возвращаем существующий ключ "
                "request_id=%s code=%s",
                self.name,
                issue_request.request_id,
                existing_key.code,
            )

            return ProviderIssueResponse(
                status="ok",
                request_id=issue_request.request_id,
                code=existing_key.code,
            )

        roll = random()

        if roll < self.error_chance:

            logger.warning(
                "Провайдер %s: выбран сценарий error request_id=%s",
                self.name,
                issue_request.request_id,
            )

            raise ProviderError(
                f"Провайдер {self.name} вернул 500"
            )

        key = await provider_key_repository.take_available_key(
            request_id=issue_request.request_id,
            order_id=issue_request.order_id,
        )

        if key is None:

            logger.warning(
                "Провайдер %s: ключи закончились request_id=%s",
                self.name,
                issue_request.request_id,
            )

            return ProviderIssueResponse(
                status='error',
                reason='out_of_stock'
            )
            # raise ProviderError(
            #     f"Провайдер {self.name}: out of stock"
            # )

        if roll < self.error_chance + self.timeout_chance:
            logger.warning(
                "Провайдер %s: выбран сценарий timeout request_id=%s",
                self.name,
                issue_request.request_id,
            )

            await asyncio.sleep(self.timeout_delay)

            raise TimeoutError(
                f"Провайдер {self.name} таймаут"
            )

        logger.info(
            "Провайдер %s: ключ выдан request_id=%s code=%s",
            self.name,
            issue_request.request_id,
            key.code,
        )

        return ProviderIssueResponse(
            status='ok',
            request_id=issue_request.request_id,
            code=key.code
        )
