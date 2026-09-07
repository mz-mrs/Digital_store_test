from pydantic import BaseModel


class ProviderIssueRequest(BaseModel):
    request_id: str
    sku: str
    order_id: str


class ProviderIssueResponse(BaseModel):
    status: str
    request_id: str | None = None
    code: str | None = None
    reason: str | None = None