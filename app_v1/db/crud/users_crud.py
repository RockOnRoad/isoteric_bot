import logging
from sqlalchemy import select, update, func, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError, SQLAlchemyError, IntegrityError

from db.models import User, Segment

logger = logging.getLogger(__name__)


async def get_user(id: int, session: AsyncSession | None = None) -> User | None:
    """
    Get user by ID.

    Args:
        id: user ID (pk)
        session: Database session

    Returns:
        User object or None
    """
    stmt = select(User).where(User.id == id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


#  --------------- GET LAST ADDED USER ---------------


async def get_last_added_user(session: AsyncSession) -> User | None:
    """Get last added user."""
    stmt = select(User).order_by(User.id.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


#  --------------- GET LAST ADDED USER ID ---------------


async def get_last_added_user_id(session: AsyncSession) -> int | None:
    """Get last added user ID."""
    stmt = select(func.max(User.id))
    result = await session.execute(stmt)
    return result.scalar()


#  --------------- UPSERT ---------------


async def upsert_user(
    *,
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    referred_id: int | None = None,
    session: AsyncSession,
) -> User:
    if user_id is None:
        raise ValueError("user_id must not be None")

    stmt = (
        insert(User)
        .values(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            referred_id=referred_id,
            segment="lead",
            # ... any other fields you want to insert
        )
        .on_conflict_do_update(
            index_elements=[User.user_id],  # this is the important part
            set_={
                "username": insert(User).excluded.username,
                "first_name": insert(User).excluded.first_name,
                "last_name": insert(User).excluded.last_name,
                # anything else you want to update
            },
        )
        .returning(User)
    )

    try:
        result = await session.execute(stmt)
        user = result.scalar_one()
        await session.commit()
        return user

    except SQLAlchemyError:
        await session.rollback()
        raise


#  --------------- ADD PARAMETERS TO USER  ---------------


async def update_user_info(
    user_id: int, data: dict, session: AsyncSession, commit: bool = True
) -> None:
    """Update user info."""
    try:
        stmt = update(User).where(User.user_id == user_id).values(data)
        await session.execute(stmt)
        if commit:
            await session.commit()
        else:
            await session.flush()

    except (DBAPIError, SQLAlchemyError) as e:
        logger.exception(
            f"Database error in update_user_info for user_id {user_id}: {e}"
        )
        try:
            await session.rollback()
        except Exception as rollback_error:
            logger.exception(
                f"Error rolling back in update_user_info: {rollback_error}"
            )
        return None


#  --------------- GET USER BY TELEGRAM ID ---------------


async def get_user_by_telegram_id(tg_id: int, session: AsyncSession) -> User | None:
    """Get user by Telegram ID."""
    stmt = select(User).where(User.user_id == tg_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


#  --------------- GET USER BALANCE ---------------


async def get_user_balance(
    user_id: int, session: AsyncSession | None = None
) -> int | None:
    """Get user balance."""
    if not session:
        logger.error("Session is required for get_user_balance")
        return None

    stmt = select(User.balance).where(User.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


#  --------------- WITHDRAW BALANCE ---------------


async def decrease_user_balance(
    user_id: int,
    amount: int,
    session: AsyncSession,
) -> int | None:
    if amount <= 0:
        raise ValueError("amount must be positive")

    stmt = (
        update(User)
        .where(User.id == user_id)
        .where(User.balance >= amount)
        .values(balance=User.balance - amount)
        .returning(User.balance)
    )

    result = await session.execute(stmt)
    new_balance = result.scalar_one_or_none()

    if new_balance is not None:
        await session.commit()

    logger.info(f"User {user_id} balance -{amount} -> {new_balance}")

    return new_balance


#  --------------- INCREASE BALANCE ---------------


async def increase_user_balance(
    user_id: int,
    amount: int,
    session: AsyncSession,
    commit: bool = True,
) -> int | None:
    if amount <= 0:
        raise ValueError("amount must be positive")

    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(balance=User.balance + amount)
        .returning(User.balance)
    )

    result = await session.execute(stmt)
    if commit:
        await session.commit()
    else:
        await session.flush()
    new_balance = result.scalar_one_or_none()

    logger.info(f"User {user_id} balance +{amount} -> {new_balance}")

    return new_balance


#  --------------- CHANGE USER BALANCE ---------------


async def change_user_balance(
    user_id: int,
    amount: int,
    session: AsyncSession,
    commit: bool = True,
) -> int | None:

    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(balance=User.balance + amount)
        .returning(User.balance)
    )

    result = await session.execute(stmt)
    if commit:
        await session.commit()
    else:
        await session.flush()
    new_balance = result.scalar_one_or_none()
    logger.info(f"User {user_id} balance {amount} -> {new_balance}")

    return new_balance


#  --------------- GET USER REFERRALS ---------------


async def get_user_referrals(user_id: int, session: AsyncSession) -> list[User]:
    """Get user referrals."""
    stmt = select(User).where(User.referred_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
