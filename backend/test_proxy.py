import requests
import os
from dotenv import load_dotenv

load_dotenv()
PROXY_URL = os.getenv("PROXY_URL")
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

print(f"Proxy URL: {PROXY_URL}")
print("Testing direct connection to google.com...")
try:
    r = requests.get("https://google.com", timeout=5)
    print(f"Success! Status: {r.status_code}")
except Exception as e:
    print(f"Failed: {e}")

if PROXY_URL:
    print(f"\nTesting proxy connection to google.com using {PROXY_URL}...")
    try:
        r = requests.get("https://google.com", proxies=proxies, timeout=10)
        print(f"Proxy Success! Status: {r.status_code}")
    except Exception as e:
        print(f"Proxy Failed: {e}")
