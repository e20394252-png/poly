import requests
import json

signer = "0xD57d3F5BB3A3a2ce4796F9B7b8a9f01F51150485"
proxy_url = "http://wxbZy0:km81Gm@194.53.190.7:8000"
proxies = {"http": proxy_url, "https": proxy_url}

# Check trades via Data API
url = f"https://data-api.polymarket.com/trades?user={signer}"
print(f"Checking {url}...")
try:
    res = requests.get(url, proxies=proxies, timeout=5)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Found {len(data)} trades.")
        if len(data) > 0:
            # Check the 'proxy' or 'owner' in the first trade
            print(f"First trade sample: {json.dumps(data[0], indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")
