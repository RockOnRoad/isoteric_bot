from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.models import UserSource


async def add_entry_to_user_sources(
    user_id: int,  # Pk ID
    source_key: str | None,
    source_value: str | None,
    session: AsyncSession,
    commit: bool = True,
) -> None:
    stmt = (
        insert(UserSource)
        .values(
            user_id=user_id,
            source_key=source_key,
            source_value=source_value,
        )
        .on_conflict_do_nothing()
    )

    try:
        await session.execute(stmt)
        if commit:
            await session.commit()
        else:
            await session.flush()
    except SQLAlchemyError:
        await session.rollback()
        raise
