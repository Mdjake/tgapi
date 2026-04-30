from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
import asyncio
import os
import base64

app = FastAPI()

API_ID = 39486590
API_HASH = "b891698655a43aa71727d96c3a26133f"
BOT_USERNAME = "@SwapiTgInfoBot"

@app.on_event("startup")
async def startup():
    global client
    # Try to load session
    encoded = os.getenv("SESSION_1")
    if encoded:
        session_data = base64.b64decode(encoded)
        with open("/tmp/session.session", "wb") as f:
            f.write(session_data)
        client = TelegramClient("/tmp/session.session", API_ID, API_HASH)
        await client.start()
        print("✅ Session loaded!")
    else:
        print("❌ No SESSION_1 env var found")

@app.post("/lookup")
async def lookup(telegram_id: str):
    await client.send_message(BOT_USERNAME, telegram_id)
    
    # Wait for response
    for _ in range(30):
        async for msg in client.iter_messages(BOT_USERNAME, limit=2):
            if msg.text and len(msg.text) > 20:
                return {"response": msg.text}
        await asyncio.sleep(1)
    
    raise HTTPException(status_code=504, detail="Timeout")
# Replace your existing @app.post("/lookup") with this:
@app.api_route("/lookup", methods=["GET", "POST"])
async def lookup(telegram_id: str):
    """Lookup Telegram ID (supports both GET and POST)"""
    if not telegram_id or not telegram_id.strip():
        raise HTTPException(status_code=400, detail="telegram_id required")
    
    telegram_id = telegram_id.strip()
    
    if not telegram_id.isdigit():
        raise HTTPException(status_code=400, detail="telegram_id must be numeric")
    
    result = await bot_api.query_bot(telegram_id)
    
    if not result["success"]:
        raise HTTPException(status_code=504, detail=result["error"])
    
    return result
