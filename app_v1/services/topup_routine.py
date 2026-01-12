import logging
from math import ceil
from typing import Optional

from aiogram import session
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import (
    create_referral_bonus,
    get_payment_by_payment_id,
    get_user,
    increase_user_balance,
    update_payment_status,
    update_user_info,
)
from db.models import Payment, User
from schemas import REFERRAL_BONUS_PERCENT

logger = logging.getLogger(__name__)


class TopupRoutine:
    """Utility for processing successful payments."""

    def __init__(self, session: AsyncSession, user_id: int):
        self.session = session
        self.user_id = user_id

    async def process_successful_payment(self, *, payment: Payment) -> Payment:
        """
        Отмечает платеж завершенным, начисляет энергию и реферальный бонус.

        Все операции выполняются в одной транзакции без промежуточных коммитов.

        Args:
            payment: Экземпляр платежа.

        Returns:
            Обновленный платеж.
        """
        if payment.status == "completed":
            return payment

        user = await get_user(id=self.user_id, session=self.session)
        if not user:
            raise ValueError(f"User with id {self.user_id} not found")

        try:
            #  Отмечаем платеж завершенным
            await update_payment_status(
                payment_id=payment.payment_id,
                status="completed",
                session=self.session,
                commit=False,
            )

            #  Начисляем энергию на баланс пользователя
            await increase_user_balance(
                user_id=self.user_id,
                amount=payment.amount,
                session=self.session,
                commit=False,
            )

            #  Переводим пользователя в сегмент "client"
            await update_user_info(
                user_id=user.user_id,
                data={"segment": "client"},
                session=self.session,
                commit=False,
            )
            await self.session.commit()

            #  Начисляем реферальный бонус пригласившему пользователю
            if user.referred_id:
                referrer: User = await get_user(
                    id=user.referred_id, session=self.session
                )
                if referrer:
                    bonus_amount = ceil(payment.amount * REFERRAL_BONUS_PERCENT)
                    if bonus_amount > 0:
                        ref_bonus_data = {
                            "ref_id": referrer.id,  # внутренний ID пригласившего
                            "referred_user_id": referrer.user_id,  # tg-id пригласившего
                            "referrer_user_id": user.user_id,  # tg-id приглашенного
                            "bonus_type": "deposit",
                            "amount": bonus_amount,
                            "deposit_rub_amount": payment.rub_amount,
                            "deposit_token_amount": payment.amount,
                            "pay_id": payment.id,
                        }
                        await create_referral_bonus(
                            data=ref_bonus_data,
                            session=self.session,
                            commit=False,
                        )

                        await increase_user_balance(
                            user_id=referrer.id,
                            amount=bonus_amount,
                            session=self.session,
                            commit=False,
                        )

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            logger.exception(
                "Failed to process successful payment %s", payment.payment_id
            )
            raise

        return payment

    async def process_payment_by_id(self, payment_id: str) -> Payment | None:
        """Утилита для запуска рутины по payment_id."""
        payment = await get_payment_by_payment_id(
            payment_id=payment_id,
            session=self.session,
        )
        if not payment:
            logger.error("Payment %s not found", payment_id)
            return None

        return await self.process_successful_payment(payment=payment)
