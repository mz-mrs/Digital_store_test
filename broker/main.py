import asyncio
import logging

from broker.consumer import consume


logging.basicConfig(level=logging.INFO)


async def main() -> None:
    await consume()


if __name__ == "__main__":
    asyncio.run(main())