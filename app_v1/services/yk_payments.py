import uuid
from typing import Optional

from yookassa import Configuration, Payment

from core.config import settings


class PaymentService:
    """Сервис для работы с платежами YooKassa."""

    def __init__(self, payment_id: Optional[str] = None):
        """
        Инициализация сервиса для работы с платежами.

        Args:
            payment_id: Опциональный ID платежа для работы с существующим платежом
        """
        Configuration.account_id = settings.yk.shop_id
        Configuration.secret_key = settings.yk.key
        self.payment_id = payment_id

    def create_payment(
        self,
        kreds: int,
        amount_rub: int,
        customer_email: str,
        chat_id: int,
        user_id: int,
        return_url: str = "https://t.me/MatrikaSoulBot",
    ) -> dict:
        """
        Создает платеж в YooKassa.

        Args:
            amount: Сумма платежа в рублях
            chat_id: ID чата пользователя
            description: Описание платежа
            return_url: URL для возврата после оплаты

        Returns:
            Словарь с данными платежа:
            {
                "payment_id": str,
                "confirmation_url": str,
                "amount": int
            }
        """

        description = (
            f"Пополнение энергии Matrika Soul Bot {user_id} ({amount_rub}₽ → {kreds}⚡️)"
        )

        payment = Payment.create(
            {
                "amount": {
                    "value": amount_rub,
                    "currency": "RUB",
                },
                "capture": True,
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url,
                },
                "receipt": {
                    "customer": {"email": customer_email},
                    "items": [
                        {
                            "quantity": "1",
                            "amount": {"value": amount_rub, "currency": "RUB"},
                            "vat_code": 1,
                            "payment_mode": "full_payment",
                            "payment_subject": "payment",
                        }
                    ],
                    "tax_system_code": 2,
                },
                "description": description,
                "metadata": {
                    "chat_id": chat_id,
                },
            },
            str(uuid.uuid4()),
        )

        # Сохраняем payment_id в экземпляр
        self.payment_id = payment.id

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "amount": amount_rub,
        }

    def get_status_success(self, payment_id: Optional[str] = None) -> Optional[dict]:
        """
        Получает статус платежа.

        Args:
            payment_id: Опциональный ID платежа. Если не указан, используется payment_id из экземпляра.

        Returns:
            Если платеж успешен (succeeded), возвращает словарь с метаданными:
            {
                "status": "succeeded",
                "metadata": dict,
                "amount": int
            }
            Иначе возвращает None

        Raises:
            ValueError: Если payment_id не указан ни в параметре, ни в экземпляре
        """
        pid = payment_id or self.payment_id
        if not pid:
            raise ValueError(
                "payment_id должен быть указан либо в __init__, либо в параметре метода"
            )

        payment = Payment.find_one(pid)

        if payment.status == "succeeded":
            return {
                "status": payment.status,
                "metadata": payment.metadata,
                "amount": payment.amount.value,
            }
        return None

    def check_payment(self, payment_id: Optional[str] = None) -> bool:
        """
        Проверяет, успешен ли платеж.

        Args:
            payment_id: Опциональный ID платежа. Если не указан, используется payment_id из экземпляра.

        Returns:
            True если платеж успешен, иначе False

        Raises:
            ValueError: Если payment_id не указан ни в параметре, ни в экземпляре
        """
        pid = payment_id or self.payment_id
        if not pid:
            raise ValueError(
                "payment_id должен быть указан либо в __init__, либо в параметре метода"
            )

        payment = Payment.find_one(pid)
        return payment.status == "succeeded"


# # Функция для обратной совместимости
# async def check_payment(payment_id: str) -> bool:
#     """
#     Проверяет статус платежа (для обратной совместимости).

#     Args:
#         payment_id: ID платежа в YooKassa

#     Returns:
#         Метаданные платежа если успешен, иначе False
#     """
#     service = PaymentService()
#     payment = Payment.find_one(payment_id)
#     if payment.status == "succeeded":
#         return payment.metadata
#     return False
