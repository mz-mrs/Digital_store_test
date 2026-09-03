import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models import ProviderKey
from app.enums import ProviderKeyStatus

logger = logging.getLogger(__name__)

KEYS_FILE = Path(__file__).parent.parent / "data" / "keys.json"

async def keys_to_db() -> None:
    with KEYS_FILE.open(encoding="utf-8") as file:
        keys_data = json.load(file)

    async with async_session_factory() as session:
        existing_keys = set(
            (
                await session.scalars(
                    select(ProviderKey.code).where(
                        ProviderKey.code.in_(keys_data['keys'])
                    )
                )
            ).all()
        )

        new_keys = [
            ProviderKey(
                code=code,
                status=ProviderKeyStatus.AVAILABLE,
            )
            for code in keys_data['keys']
            if code not in existing_keys
        ]

        session.add_all(new_keys)
        await session.commit()

        logger.info(
            "Успешная загрузка ключей провадера в базу, добавлено %s ключей",
        len(new_keys)
        )


if __name__ == "__main__":
    asyncio.run(keys_to_db())