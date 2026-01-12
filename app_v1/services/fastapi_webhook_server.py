import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from yookassa import Payment as YKPayment, Webhook

from core.config import bot
from db.crud import get_payment_by_payment_id, get_user
from db.database import AsyncSessionLocal


# --- FastAPI app ---
app = FastAPI()


@app.post("/webhook/yookassa")
async def webhook(request: Request):
    payload = await request.json()
    print(payload)
    # {
    #     "id": "e44e8088-bd73-43b1-959a-954f3a7d0c54",
    #     "event": "payment.succeeded",
    #     "url": "https://www.example.com/notification_url"
    # }

    id = payload.get("id")
    event = payload.get("event")
    url = payload.get("url")

    # print(payload)
    # user_id = (
    #     payload.get("event", {}).get("object", {}).get("metadata", {}).get("user_id")
    # )
    # status = payload.get("event", {}).get("object", {}).get("status")

    # Add your processing logic here
    print(f": {id}, {event}, {url}")
    async with AsyncSessionLocal() as session:

        payment = await get_payment_by_payment_id(id, session=session)
        user = await get_user(payment.user_id, session=session)
        user_id = user.user_id
        user = await get_user(payment.user_id)
        user_id = user.user_id

    # Не блокируем ответ телеграм-запросом, запускаем отправку в фоне
    if user_id:
        asyncio.create_task(
            bot.send_message(
                chat_id=user_id,
                text=(
                    "Payment received!\n\n",
                    f"Id: {id}\n",
                    f"Event: {event}\n",
                    f"Url: {url}\n",
                ),
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
