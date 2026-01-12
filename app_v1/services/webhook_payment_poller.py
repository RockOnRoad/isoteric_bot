"""Слушатель webhook'ов ЮKassa для входящих платежей."""

import base64
import logging
import ssl
from ipaddress import ip_address, ip_network, IPv4Network
from pathlib import Path

from aiohttp import web, web_request
from aiohttp.web_response import Response

from core.config import settings
from db.crud import get_payment_by_payment_id, update_payment_status
from db.database import AsyncSessionLocal
from services.topup_routine import TopupRoutine

logger = logging.getLogger(__name__)


class WebhookServer:
    """HTTP сервер для приема уведомлений о платежах."""

    def __init__(
        self,
        port: int = 8000,
        bot=None,
        ssl_cert_path: str | None = None,
        ssl_key_path: str | None = None,
    ):
        self.port = port
        self.bot = bot
        root_dir = Path(__file__).resolve().parents[2]
        default_cert = root_dir / "ssl" / "certificate.pem"
        default_key = root_dir / "ssl" / "private.key"

        self.ssl_cert_path = ssl_cert_path or (
            str(default_cert) if default_cert.exists() else None
        )
        self.ssl_key_path = ssl_key_path or (
            str(default_key) if default_key.exists() else None
        )
        self.allowed_subnets: tuple[IPv4Network, ...] = (
            ip_network("127.0.0.0/8"),  # localhost
            ip_network("185.6.233.0/24"),
            ip_network("185.6.234.0/24"),
            ip_network("77.75.153.0/25"),
            ip_network("172.16.0.0/12"),
        )
        creds = f"{settings.yk.shop_id}:{settings.yk.key}"
        token = base64.b64encode(creds.encode()).decode()
        self.expected_auth_header = f"Basic {token}"

        self.app = web.Application()
        self.app.router.add_post("/webhook/yookassa", self.handle_yookassa_webhook)
        self.app.router.add_get("/health", self.health_check)

    def _is_request_allowed(self, request: web_request.Request) -> bool:
        """Проверяет IP и заголовок Authorization без лишних проходов."""
        client_ip = request.headers.get("X-Forwarded-For", request.remote or "")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        try:
            ip_obj = ip_address(client_ip)
        except ValueError:
            logger.warning("Webhook rejected: IP not recognized (%s)", client_ip)
            return False

        if not any(ip_obj in subnet for subnet in self.allowed_subnets):
            logger.warning(
                "Webhook rejected: IP %s is outside allowed ranges", client_ip
            )
            return False

        auth_header = request.headers.get("Authorization", "")
        if auth_header != self.expected_auth_header:
            logger.warning("Webhook rejected: invalid Authorization header")
            return False

        return True

    async def handle_yookassa_webhook(self, request: web_request.Request) -> Response:
        """Обработчик webhook'а от ЮKassa."""
        body = await request.text()

        # Безопасность: сверяем IP и заголовок авторизации
        if not self._is_request_allowed(request):
            return Response(status=401, text="Unauthorized")

        try:
            payload = await request.json()
        except Exception:
            logger.warning("Invalid JSON in webhook: %s", body)
            return Response(status=400, text="Bad Request")

        event = payload.get("event")
        payment_data: dict = payload.get("object", {}) or {}
        payment_id = payment_data.get("id")
        status = payment_data.get("status")

        if not payment_id or not status:
            logger.warning("Webhook missing required fields: %s", payload)
            return Response(status=400, text="Missing payment data")

        logger.info(
            "Webhook received: event=%s payment_id=%s status=%s",
            event,
            payment_id,
            status,
        )

        try:
            if status == "succeeded":
                handled = await self._handle_successful_payment(payment_id)
                return Response(status=200 if handled else 500, text="OK")

            if status == "canceled":
                await self._handle_canceled_payment(payment_id)
                return Response(status=200, text="OK")

            logger.info(
                "Webhook with unexpected status %s for payment %s", status, payment_id
            )
            return Response(status=200, text="Ignored")
        except Exception as exc:
            logger.exception("Error processing webhook %s: %s", payment_id, exc)
            return Response(status=500, text="Internal Server Error")

    async def _handle_successful_payment(self, payment_id: str) -> bool:
        """Отмечает платеж успешным и начисляет баланс."""
        async with AsyncSessionLocal() as session:
            payment = await get_payment_by_payment_id(payment_id, session)

            if not payment:
                logger.warning("Payment %s not found in database", payment_id)
                return True  # Возвращаем 200, чтобы не получать повторов

            if payment.status == "completed":
                logger.info("Payment %s was already processed earlier", payment_id)
                return True

            # Фиксируем успешный статус перед начислением
            await update_payment_status(
                payment_id=payment_id,
                status="succeeded",
                session=session,
                commit=False,
            )

            topup_routine = TopupRoutine(session=session, user_id=payment.user_id)
            await topup_routine.process_successful_payment(payment=payment)

            logger.info("Payment %s processed via webhook", payment_id)
            return True

    async def _handle_canceled_payment(self, payment_id: str) -> None:
        """Помечает платеж отмененным."""
        async with AsyncSessionLocal() as session:
            payment = await get_payment_by_payment_id(payment_id, session)
            if not payment:
                logger.warning("Payment %s not found for cancellation", payment_id)
                return

            if payment.status == "canceled":
                return

            await update_payment_status(
                payment_id=payment_id,
                status="canceled",
                session=session,
            )
            logger.info("Payment %s marked as canceled", payment_id)

    async def health_check(self, request: web_request.Request) -> Response:
        """Проверка здоровья сервера."""
        return Response(status=200, text="OK")

    async def start(self):
        """Запуск сервера."""
        runner = web.AppRunner(self.app)
        await runner.setup()

        # Настройка SSL если указаны пути к сертификатам
        ssl_context = None
        if self.ssl_cert_path and self.ssl_key_path:
            try:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(self.ssl_cert_path, self.ssl_key_path)
                logger.info("SSL certificate loaded: %s", self.ssl_cert_path)
            except Exception as exc:
                logger.error("Error loading SSL certificate: %s", exc)
                logger.warning("Starting without SSL (HTTP only)")
                ssl_context = None

        site = web.TCPSite(runner, "0.0.0.0", self.port, ssl_context=ssl_context)
        await site.start()

        protocol = "HTTPS" if ssl_context else "HTTP"
        logger.info("Webhook server started on port %s (%s)", self.port, protocol)
        logger.info(
            "Webhook URL: %s://%s:%s/webhook/yookassa",
            "https" if ssl_context else "http",
            "localhost",
            self.port,
        )

    async def stop(self):
        """Остановка сервера."""
        try:
            await self.app.cleanup()
            logger.info("Webhook server stopped")
        except Exception as exc:
            logger.error("Error stopping webhook server: %s", exc)


# Глобальный экземпляр для быстрого запуска
webhook_server = WebhookServer()
