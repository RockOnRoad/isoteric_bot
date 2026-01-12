import logging
from typing import Optional

import asyncio

from db.database import AsyncSessionLocal
from db.crud import (
    get_pending_payments,
    update_payment_status,
)
from services.yk_payments import PaymentService
from services.topup_routine import TopupRoutine

logger = logging.getLogger(__name__)


class PaymentPoller:
    """Сервис для автоматической проверки статусов платежей."""

    def __init__(self, poll_interval: int = 40):
        """
        Инициализация опроса платежей.

        Args:
            poll_interval: Интервал проверки в секундах (по умолчанию 30)
        """
        self.poll_interval = poll_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def check_pending_payments(self) -> None:
        """Проверяет все незавершенные платежи и обновляет их статусы."""
        async with AsyncSessionLocal() as session:
            try:
                pending_payments = await get_pending_payments(session=session)

                if not pending_payments:
                    return

                logger.info(f"Checking {len(pending_payments)} pending payments...")

                for payment in pending_payments:
                    try:
                        payment_service = PaymentService(payment_id=payment.payment_id)
                        status_success_data = payment_service.get_status_success()

                        if status_success_data:

                            topup_routine = TopupRoutine(
                                session=session, user_id=payment.user_id
                            )
                            await topup_routine.process_successful_payment(
                                payment=payment
                            )

                            logger.info(
                                f"Payment {payment.payment_id} completed. \n"
                                f"Balance increased for user {payment.user_id}"
                            )
                        else:
                            # Проверяем, не отменен ли платеж
                            from yookassa import Payment as YKPayment

                            yk_payment = YKPayment.find_one(payment.payment_id)

                            if yk_payment.status == "canceled":
                                await update_payment_status(
                                    payment_id=payment.payment_id,
                                    status="canceled",
                                    session=session,
                                )
                                logger.info(
                                    f"Payment {payment.payment_id} was canceled"
                                )

                    except Exception as e:
                        logger.error(
                            f"Error checking payment {payment.payment_id}: {e}",
                            exc_info=True,
                        )
                        continue

            except Exception as e:
                logger.error(f"Error in payment poller: {e}", exc_info=True)

    async def start(self) -> None:
        """Запускает фоновую задачу опроса платежей."""
        if self.is_running:
            logger.warning("Payment poller is already running")
            return

        self.is_running = True
        logger.info(f"Starting payment poller (interval: {self.poll_interval}s)")

        async def poll_loop():
            while self.is_running:
                try:
                    await self.check_pending_payments()
                except Exception as e:
                    logger.error(f"Error in poll loop: {e}", exc_info=True)

                await asyncio.sleep(self.poll_interval)

        self._task = asyncio.create_task(poll_loop())

    async def stop(self) -> None:
        """Останавливает фоновую задачу опроса платежей."""
        if not self.is_running:
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Payment poller stopped")
