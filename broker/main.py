import asyncio
import logging

from broker.consumer import consume
from broker.dlq_consumer import consume_dlq
from broker.recovery_consumer import recover

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    await asyncio.gather(
        consume(),
        consume_dlq(),
        recover()
    )


if __name__ == "__main__":
    asyncio.run(main())