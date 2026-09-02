from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends

from app.db.session import get_session

app = FastAPI()


@app.get("/test-db")
async def test_db(
        session: AsyncSession = Depends(get_session)
):
    result = await session.execute(text("SELECT 1"))

    return {"database": result.scalar_one()}
