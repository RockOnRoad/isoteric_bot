import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from core.config import bot


# --- FastAPI app ---
app = FastAPI()


@app.post("/webhook/yookassa")
async def webhook(request: Request):
    payload = await request.json()
    print(payload)
    user_id = payload.get("object", {}).get("metadata", {}).get("user_id")
    # Add your processing logic here
    await bot.send_message(user_id, "Payment received!")
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
