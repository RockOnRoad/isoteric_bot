import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.models.payment import Payment, PaymentStatus

logger = logging.getLogger(__name__)


async def create_payment(
    *,
    user_id: int,
    payment_id: str,
    amount: int,
    rub_amount: int,
    status: PaymentStatus | None = None,
    session: AsyncSession,
) -> Payment:
    """
    Создает новую запись о платеже в БД.

    Args:
        user_id: Telegram ID пользователя
        payment_id: ID платежа от YooKassa
        amount: Количество кредитов
        rub_amount: Количество рублей
        status: Статус платежа (по умолчанию "pending")
        session: Сессия БД

    Returns:
        Созданный объект Payment
    """
    try:
        payment = Payment(
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            rub_amount=rub_amount,
            status=status,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating payment: {e}")
        raise


async def get_payment_by_payment_id(
    payment_id: str,
    session: AsyncSession,
) -> Optional[Payment]:
    """
    Получает платеж по ID платежа от YooKassa.

    Args:
        payment_id: ID платежа от YooKassa
        session: Сессия БД

    Returns:
        Объект Payment или None
    """
    stmt = select(Payment).where(Payment.payment_id == payment_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_payment_status(
    *,
    payment_id: str,
    status: PaymentStatus,
    completed_at: Optional[datetime] = None,
    session: AsyncSession,
) -> Optional[Payment]:
    """
    Обновляет статус платежа.

    Args:
        payment_id: ID платежа от YooKassa
        status: Новый статус платежа
        completed_at: Время завершения платежа (опционально)
        session: Сессия БД

    Returns:
        Обновленный объект Payment или None
    """
    try:
        payment = await get_payment_by_payment_id(payment_id, session)
        if not payment:
            return None

        payment.status = status
        if completed_at:
            payment.completed_at = completed_at
        elif status == "completed":
            # Используем func.now() для единообразия с created_at (server_default=func.now())
            stmt = (
                update(Payment)
                .where(Payment.payment_id == payment_id)
                .values(completed_at=func.now())
            )
            await session.execute(stmt)

        await session.commit()
        await session.refresh(payment)
        return payment
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error updating payment status: {e}")
        raise


async def get_pending_payments(
    session: AsyncSession,
) -> list[Payment]:
    """
    Получает все платежи со статусом "pending".

    Args:
        session: Сессия БД

    Returns:
        Список платежей со статусом "pending"
    """
    stmt = select(Payment).where(Payment.status == "pending")
    result = await session.execute(stmt)
    return list(result.scalars().all())
