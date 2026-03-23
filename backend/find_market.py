import requests
import json

query = "Shanghai temperature"
proxy_url = "http://wxbZy0:km81Gm@194.53.190.7:8000"
proxies = {"http": proxy_url, "https": proxy_url}

url = f"https://gamma-api.polymarket.com/markets?query={query}"
print(f"Searching for market: {query}...")
try:
    res = requests.get(url, proxies=proxies, timeout=5)
    if res.status_code == 200:
        data = res.json()
        print(f"Found {len(data)} markets.")
        if len(data) > 0:
            for m in data:
                if "Shanghai" in m.get("question", ""):
                    print(f"Market Found: {m.get('question')}")
                    print(f"Token IDs: {m.get('clobTokenIds')}")
                    print(f"Condition ID: {m.get('conditionId')}")
except Exception as e:
    print(f"Error: {e}")
