import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# from yookassa import Payment as YKPayment, Webhook

from core.config import bot, YK_TRUSTED_NETWORKS
from db.crud import get_payment_by_payment_id, get_user
from db.database import AsyncSessionLocal
from services.topup_routine import TopupRoutine


# --- FastAPI app ---
app = FastAPI()


@app.post("/webhook/yookassa")
async def webhook(request: Request):

    client_ip = request.client.host

    # Проверка - принадлежит ли IP доверенным сетям
    import ipaddress

    ip = ipaddress.ip_address(client_ip)
    allowed = False
    for net in YK_TRUSTED_NETWORKS:
        if ip in ipaddress.ip_network(net):
            allowed = True
            break

    if not allowed:
        # либо 403 Forbidden, либо сразу return
        return JSONResponse({"message": "Forbidden"}, status_code=403)

    payload = await request.json()
    print(payload)

    status = payload.get("object", {}).get("status")
    id = payload.get("object", {}).get("id")
    chat_id = payload.get("object", {}).get("metadata", {}).get("chat_id")

    if status == "succeeded":
        async with AsyncSessionLocal() as session:

            payment = await get_payment_by_payment_id(id, session=session)
            user = await get_user(payment.user_id, session=session)
            user_id = user.id

            topup_routine = TopupRoutine(session=session, user_id=user_id)
            await topup_routine.process_successful_payment(payment=payment)

        # Не блокируем ответ телеграм-запросом, запускаем отправку в фоне
        if chat_id:
            asyncio.create_task(
                bot.send_message(
                    chat_id=chat_id,
                    text=(f"+ {payment.amount} энергии ⚡️"),
                )
            )

    return JSONResponse({"message": "Webhook received successfully"}, status_code=200)


# --- Function to run FastAPI in background ---


async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",  # debug, info, warning, error, critical
        ssl_keyfile="certs/key.pem",
        ssl_certfile="certs/cert.pem",
    )
    server = uvicorn.Server(config)
    await server.serve()  # this is async and will block, so run in a task
