import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request

from core.config import bot


# --- FastAPI app ---
app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    print(payload)
    # Add your processing logic here
    await bot.send_message(238163604, "Payment received!")
    return {"message": "Webhook received successfully"}


# --- Function to run FastAPI in background ---


async def start_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()  # this is async and will block, so run in a task
