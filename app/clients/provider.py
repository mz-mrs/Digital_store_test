import httpx

from app.schemas.provider import (
    ProviderIssueRequest,
    ProviderIssueResponse,
)

class ProviderError(Exception):
    pass

class ProviderClient:
    def __init__(
        self,
        name: str,
        base_url: str,
        timeout: float = 3.0,
    ) -> None:
        self.name = name
        self.base_url = base_url
        self.timeout = timeout

    async def issue(
        self,
        issue_request: ProviderIssueRequest,
    ) -> ProviderIssueResponse:

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/issue",
                json=issue_request.model_dump(),
            )

        response.raise_for_status()

        return ProviderIssueResponse.model_validate(
            response.json()
        )