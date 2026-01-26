from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from db.models import UserBonus


#  --------------- UPSERT USER BONUS ---------------


async def upsert_user_bonus(
    user_id: int,
    bonus_name: str,
    amount: int,
    session: AsyncSession,
    deposited: bool = False,
) -> None:

    stmt = (
        insert(UserBonus)
        .values(
            user_id=user_id,
            bonus_name=bonus_name,
            amount=amount,
            deposited=deposited,
        )
        .on_conflict_do_update(
            index_elements=[UserBonus.user_id, UserBonus.bonus_name],
            set_={
                "deposited": deposited,
            },
        )
        .returning(UserBonus)
    )
    result = await session.execute(stmt)
    user_bonus = result.scalar_one_or_none()
    await session.commit()
    return user_bonus


#  --------------- ADD USER BONUS ---------------


async def add_user_bonus(
    user_id: int,  # Pk ID
    bonus_name: str,
    amount: int,
    session: AsyncSession,
    deposited: bool = False,
    commit: bool = True,
) -> None:
    stmt = (
        insert(UserBonus)
        .values(
            user_id=user_id,
            bonus_name=bonus_name,
            deposited=deposited,
            amount=amount,
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


#  --------------- GET USER BONUS BY NAME ---------------


async def get_user_bonus_by_name(
    user_id: int,
    bonus_name: str,
    session: AsyncSession,
) -> UserBonus | None:
    stmt = select(UserBonus).where(
        UserBonus.user_id == user_id, UserBonus.bonus_name == bonus_name
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
