import requests
import json

target = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"
proxy_url = "http://wxbZy0:km81Gm@194.53.190.7:8000"
proxies = {"http": proxy_url, "https": proxy_url}

endpoints = [
    f"https://data-api.polymarket.com/positions?user={target}",
    f"https://data-api.polymarket.com/profiles?wallet={target}"
]

for url in endpoints:
    print(f"Checking {url}...")
    try:
        res = requests.get(url, proxies=proxies, timeout=5)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(f"Data: {res.text[:1000]}...")
    except Exception as e:
        print(f"Error: {e}")
