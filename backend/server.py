from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
from datetime import datetime
from bot import run_bot_loop, TRADE_AMOUNT_USDC, POLL_INTERVAL_SECONDS

print(f"[{datetime.now().isoformat()}] server.py: Bot module imported successfully.")

app = FastAPI(title="Polymarket Bot Dashboard API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state imported from bot
from bot import global_state, run_bot_loop
from bot import redeem_resolved_position
import threading

bot_thread: threading.Thread | None = None

@app.on_event("startup")
async def startup_event():
    """Auto-start the bot engine when the server starts."""
    global bot_thread
    if global_state.status != "running":
        print(f"[{datetime.now().isoformat()}] Auto-starting bot thread on server startup...")
        global_state.status = "running"
        global_state.stop_event.clear()
        bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
        bot_thread.start()

@app.get("/api/status")
async def get_status(background_tasks: BackgroundTasks):
    from bot import update_balance_and_positions
    # Run update in background so API remains fast
    background_tasks.add_task(update_balance_and_positions)
        
    return {
        "status": global_state.status,
        "current_action": getattr(global_state, "current_action", "System Initialized"),
        "latency_ms": getattr(global_state, "latency_ms", 0),
        "active_proxy": getattr(global_state, "active_proxy", "Direct"),
        "last_poll": global_state.last_poll,
        "trades_count": global_state.trades_count,
        "balance": global_state.balance,
        "realized_profit": global_state.realized_profit,
        "recent_trades": global_state.recent_trades,
        "opportunities": global_state.opportunities,
        "positions": global_state.positions,
        "config": global_state.config,
        "logs": global_state.logs
    }

@app.post("/api/start")
async def start_bot():
    if global_state.status == "running":
        return {"message": "Bot is already running"}
    
    # Start bot loop in a separate thread so it doesn't block the API
    global bot_thread
    global_state.status = "running"
    global_state.stop_event.clear()
    bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
    bot_thread.start()
    
    return {"message": "Bot started"}

@app.post("/api/stop")
async def stop_bot():
    global_state.status = "stopped"
    global_state.stop_event.set()
    return {"message": "Bot stop requested"}


from pydantic import BaseModel
from typing import Optional

class SellRequest(BaseModel):
    token_id: Optional[str] = None

@app.post("/api/sell_position")
async def api_sell_position(req: SellRequest):
    from bot import force_sell_position
    res = force_sell_position(req.token_id)
    return res


@app.post("/api/redeem")
async def redeem_position():
    """
    Redeem (claim) collateral for resolved positions.
    Currently redeems the first tracked position.
    """
    if not global_state.positions:
        return {"ok": False, "error": "No positions to redeem"}

    pos = global_state.positions[0]
    res = redeem_resolved_position(pos)
    return res

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
