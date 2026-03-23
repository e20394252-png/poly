import os
import sys
from datetime import datetime

print(f"[{datetime.now().isoformat()}] Importing bot module...")
try:
    import bot
    print(f"[{datetime.now().isoformat()}] Bot module imported successfully!")
    
    print(f"[{datetime.now().isoformat()}] Calling update_balance_and_positions()...")
    bot.update_balance_and_positions()
    print(f"[{datetime.now().isoformat()}] Call finished!")
    print(f"Balance: {bot.global_state.balance}")
    print(f"Positions: {bot.global_state.positions}")
    
except Exception as e:
    import traceback
    print(f"[{datetime.now().isoformat()}] CRASH: {e}")
    traceback.print_exc()
