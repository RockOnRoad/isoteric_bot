from sqlalchemy.ext.asyncio import AsyncSession

from core.config import devs
from db.models import GenerationHistory
from .users_crud import get_user


#  --------------- CREATE ---------------


async def add_generation(
    *,
    session: AsyncSession,
    commit: bool = True,
    **kwargs,
) -> GenerationHistory:
    """Add a new generation to the database."""
    user = await get_user(kwargs["user_id"], session)
    # if user.user_id not in [int(dev) for dev in devs]:
    generation = GenerationHistory(**kwargs)
    session.add(generation)
    if commit:
        await session.commit()
    else:
        await session.flush()
    await session.refresh(generation)
    return generation
    # return None
