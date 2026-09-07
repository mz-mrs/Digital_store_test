
def generate_request_id(order_id: str, attempt: int) -> str:
    return f"req_{order_id}-{attempt}"

