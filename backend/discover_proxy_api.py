import requests
import json

signer = "0xD57d3F5BB3A3a2ce4796F9B7b8a9f01F51150485"
proxy_url = "http://wxbZy0:km81Gm@194.53.190.7:8000"
proxies = {"http": proxy_url, "https": proxy_url}

endpoints = [
    f"https://data-api.polymarket.com/positions?user={signer}",
    f"https://gamma-api.polymarket.com/users?address={signer}",
    f"https://gamma-api.polymarket.com/profiles?address={signer}",
    f"https://data-api.polymarket.com/profiles?wallet={signer}"
]

for url in endpoints:
    print(f"Checking {url}...")
    try:
        res = requests.get(url, proxies=proxies, timeout=5)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(f"Data: {res.text[:500]}...")
    except Exception as e:
        print(f"Error: {e}")
