import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
PROXY_URL = os.getenv("PROXY_URL")
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

addr = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"
url = f"https://data-api.polymarket.com/positions?user={addr}"

print(f"Fetching positions for {addr}...")
try:
    response = requests.get(url, proxies=proxies, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
