import requests
import json

query = "Shanghai"
proxy_url = "http://wxbZy0:km81Gm@194.53.190.7:8000"
proxies = {"http": proxy_url, "https": proxy_url}

url = f"https://gamma-api.polymarket.com/markets?query={query}"
try:
    res = requests.get(url, proxies=proxies, timeout=5)
    if res.status_code == 200:
        data = res.json()
        for m in data:
            if "highest temperature" in m.get("question", "").lower():
                print(f"Match: {m.get('question')}")
                print(f"Condition: {m.get('conditionId')}")
                print(f"Token IDs: {m.get('clobTokenIds')}")
                # Get more details for tokens
                tokens = m.get('clobTokenIds')
                if tokens:
                    token_list = json.loads(tokens)
                    print(f"Simplified Tokens: {token_list}")
except Exception as e:
    print(f"Error: {e}")
