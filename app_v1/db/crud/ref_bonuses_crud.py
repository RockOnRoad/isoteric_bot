import logging

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.models import ReferralBonus

logger = logging.getLogger(__name__)


async def create_referral_bonus(
    *,
    data: dict,
    session: AsyncSession,
) -> ReferralBonus:
    stmt = (
        insert(ReferralBonus)
        .values(
            **data,
        )
        .returning(ReferralBonus)
    )
    try:
        result = await session.execute(stmt)
        referral_bonus = result.scalar_one()
        await session.commit()
        return referral_bonus
    except SQLAlchemyError:
        await session.rollback()
        raise


async def get_user_referral_bonuses_total(
    user_id: int,
    session: AsyncSession,
) -> int:
    """
    Get total sum of referral bonuses for a user.

    Note: This function searches by ref_id which should match the user's internal ID.
    If the relationship in the model is correct, ref_id should store the referrer's ID.
    """
    stmt = select(func.coalesce(func.sum(ReferralBonus.amount), 0)).where(
        ReferralBonus.ref_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one() or 0
