from fastapi import FastAPI, HTTPException
from telethon import TelegramClient, events
import asyncio
import time
import os
import base64
from datetime import datetime

app = FastAPI()

# Configuration
API_ID = int(os.getenv("API_ID", "39486590"))
API_HASH = os.getenv("API_HASH", "b891698655a43aa71727d96c3a26133f")
BOT_USERNAME = "@SwapiTgInfoBot"
REQUEST_TIMEOUT = 25

class SessionLoader:
    """Load sessions from environment variables"""
    
    @staticmethod
    def decode_session_from_env(session_num):
        """Decode session from env var"""
        session_b64 = os.getenv(f"SESSION_{session_num}")
        if session_b64:
            try:
                session_data = base64.b64decode(session_b64)
                return session_data
            except:
                return None
        return None
    
    @staticmethod
    def get_session_path(session_num):
        """Get temporary file path for session"""
        session_data = SessionLoader.decode_session_from_env(session_num)
        
        if not session_data:
            return None
        
        # Create temp file (Vercel /tmp directory)
        temp_path = f"/tmp/telegram_session_{session_num}.session"
        with open(temp_path, "wb") as f:
            f.write(session_data)
        
        return temp_path

class TelegramBotAPI:
    def __init__(self):
        self.clients = []
        self.current_session = 0
        self.lock = asyncio.Lock()
        self.initialized = False
    
    async def initialize(self):
        """Load all sessions from environment variables"""
        if self.initialized:
            return True
        
        print(f"🔧 Loading sessions from environment variables...")
        
        # Try to load up to 5 sessions
        for i in range(1, 6):
            session_path = SessionLoader.get_session_path(i)
            if session_path:
                try:
                    client = TelegramClient(session_path, API_ID, API_HASH)
                    await client.start()
                    self.clients.append(client)
                    print(f"✅ Session {i} loaded")
                except Exception as e:
                    print(f"❌ Failed to load session {i}: {e}")
            else:
                if i == 1:
                    print("❌ No sessions found in environment variables!")
                break
        
        if not self.clients:
            return False
        
        self.initialized = True
        print(f"✅ {len(self.clients)} sessions ready")
        return True
    
    async def query_bot(self, telegram_id: str):
        """Send query to bot"""
        if not self.initialized:
            await self.initialize()
        
        if not self.clients:
            return {
                "success": False,
                "error": "No sessions available"
            }
        
        start_time = time.time()
        
        # Round robin session selection
        async with self.lock:
            client = self.clients[self.current_session % len(self.clients)]
            self.current_session += 1
        
        try:
            # Send message
            await client.send_message(BOT_USERNAME, telegram_id)
            
            # Wait for response
            response = None
            timeout = REQUEST_TIMEOUT
            start_wait = time.time()
            
            while time.time() - start_wait < timeout:
                async for message in client.iter_messages(BOT_USERNAME, limit=5):
                    if message.text and len(message.text) > 20 and "finding" not in message.text.lower():
                        response = message.text
                        break
                
                if response:
                    break
                
                await asyncio.sleep(0.5)
            
            total_time = time.time() - start_time
            
            if response:
                return {
                    "success": True,
                    "response": response,
                    "telegram_id": telegram_id,
                    "total_time_ms": round(total_time * 1000, 2),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "No response from bot",
                    "telegram_id": telegram_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "telegram_id": telegram_id
            }
    
    async def close(self):
        """Close all sessions"""
        for client in self.clients:
            await client.disconnect()

# Global instance
bot_api = TelegramBotAPI()

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    await bot_api.initialize()

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await bot_api.close()

@app.get("/")
async def root():
    return {
        "message": "Telegram Bot API is running",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "sessions": len(bot_api.clients),
        "initialized": bot_api.initialized,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    return {
        "total_sessions": len(bot_api.clients),
        "initialized": bot_api.initialized,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/lookup")
async def lookup(telegram_id: str):
    """Lookup Telegram ID"""
    if not telegram_id or not telegram_id.strip():
        raise HTTPException(status_code=400, detail="telegram_id required")
    
    telegram_id = telegram_id.strip()
    
    if not telegram_id.isdigit():
        raise HTTPException(status_code=400, detail="telegram_id must be numeric")
    
    result = await bot_api.query_bot(telegram_id)
    
    if not result["success"]:
        raise HTTPException(status_code=504, detail=result["error"])
    
    return result
