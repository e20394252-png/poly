import sys
import os

print("DEBUG: run_bot_debug.py started.", flush=True)

# Добавляем путь к backend, чтобы bot.py мог найти свои зависимости
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

print("DEBUG: Path inserted, attempting to import bot.", flush=True)
import bot
print("DEBUG: bot module imported successfully.", flush=True)

if __name__ == "__main__":
    print("DEBUG: Starting bot.run_bot_loop() directly...", flush=True)
    bot.run_bot_loop()
print("DEBUG: run_bot_debug.py finished.", flush=True)