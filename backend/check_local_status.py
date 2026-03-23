import requests
import json

try:
    # Use localhost directly, bypass any proxy environment variables
    r = requests.get("http://127.0.0.1:8000/api/status", timeout=5, proxies={"http": None, "https": None})
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
