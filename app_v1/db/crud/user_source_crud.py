from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.models import UserSource


async def add_entry_to_user_sources(
    user_id: int,
    source: str | None,
    session: AsyncSession,
) -> None:
    stmt = (
        insert(UserSource)
        .values(
            user_id=user_id,
            source_key=source,
            # source_value=...,
        )
        .on_conflict_do_nothing()
    )

    try:
        await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise
