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

    status = payload.get("object", {}).get("status")
    id = payload.get("object", {}).get("id")
    user_id = payload.get("object", {}).get("metadata", {}).get("chat_id")

    # Не блокируем ответ телеграм-запросом, запускаем отправку в фоне
    if user_id:
        asyncio.create_task(
            bot.send_message(
                chat_id=user_id,
                text=(
                    "Payment received!\n\n",
                    f"Id: {id}\n",
                    f"Status: {status}\n",
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
