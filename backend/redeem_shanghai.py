"""
Redeem the resolved Shanghai position through Polymarket Relayer API.
This uses the Builder/Relayer API to execute a gasless redemption
through the proxy wallet.

Usage: Set RELAYER_API_KEY, RELAYER_API_SECRET, RELAYER_API_PASSPHRASE in .env
       then run: python redeem_shanghai.py
"""
import os
import json
import time
import hmac
import hashlib
import base64
import requests
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

from dotenv import load_dotenv

load_dotenv()

# Config
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RELAYER_API_KEY = os.getenv("RELAYER_API_KEY")
RELAYER_API_SECRET = os.getenv("RELAYER_API_SECRET")  
RELAYER_API_PASSPHRASE = os.getenv("RELAYER_API_PASSPHRASE")
PROXY_URL = os.getenv("PROXY_URL")

RELAYER_HOST = "https://relayer-v2.polymarket.com"
PROXY_ADDR = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"
SIGNER_ADDR = "0xD57d3F5BB3A3a2ce4796F9B7b8a9f01F51150485"

# Shanghai position data
CONDITION_ID = "0x157f2aef23bfb36b5cd989fa23ac515197d16e77d676c7d04cff2b0c3da32545"

def create_hmac_signature(secret: str, timestamp: str, method: str, path: str, body: str = "") -> str:
    """Create HMAC-SHA256 signature for Relayer API authentication."""
    message = timestamp + method.upper() + path + body
    secret_bytes = base64.b64decode(secret)
    signature = hmac.new(secret_bytes, message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(signature.digest()).decode('utf-8')

def relayer_request(method: str, path: str, body: dict = None):
    """Make authenticated request to Relayer API."""
    if not RELAYER_API_KEY:
        print("ERROR: Missing RELAYER_API_KEY in .env!")
        return None
    
    timestamp = str(int(time.time()))
    body_str = json.dumps(body) if body else ""
    
    headers = {
        "RELAYER_API_KEY": RELAYER_API_KEY,
        "RELAYER_API_KEY_ADDRESS": SIGNER_ADDR,
        "Content-Type": "application/json",
    }
    
    url = RELAYER_HOST + path
    print(f"\n{method} {url}")
    print(f"Headers: {json.dumps({k: v[:20]+'...' if len(v)>20 else v for k,v in headers.items()}, indent=2)}")
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    
    if method == "GET":
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=60)
    else:
        resp = requests.post(url, headers=headers, data=body_str, proxies=proxies, timeout=60)
    
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except:
        print(f"Response text: {resp.text[:500]}")
        return None

def main():
    print("=" * 60)
    print("Shanghai Position Redemption via Relayer API")
    print("=" * 60)
    print(f"Signer:      {SIGNER_ADDR}")
    print(f"Proxy Wallet: {PROXY_ADDR}")
    print(f"Condition ID: {CONDITION_ID}")
    
    # Step 1: Check what endpoints are available
    print("\n--- Step 1: Check Relayer API ---")
    
    # Try to find redeemable positions
    print("\nChecking positions via Data API...")
    r = requests.get(f"https://data-api.polymarket.com/positions?user={PROXY_ADDR}&redeemable=true", timeout=10)
    positions = r.json()
    print(f"Found {len(positions)} redeemable positions")
    for p in positions:
        if float(p.get('size', 0)) > 0:
            print(f"  -> {p.get('title')}: {p.get('size')} shares, outcome={p.get('outcome')}")
    
    # Step 2: Try redemption via Relayer
    print("\n--- Step 2: Attempt Redemption ---")
    
    # The relayer endpoint for CTF operations
    # Based on docs: POST /relay with transaction type PROXY for proxy wallets
    redeem_body = {
        "type": "PROXY",
        "data": {
            "to": PROXY_ADDR,
            "conditionId": CONDITION_ID,
            "indexSets": [1, 2],  # Redeem both outcomes (only winner pays out)
        }
    }
    
    result = relayer_request("POST", "/redeem", redeem_body)
    
    if result:
        print(f"\n[OK] Redemption submitted!")
    else:
        print(f"\n[FAIL] Redemption failed on /redeem. Trying alternative endpoint /relay...")
        
        # Alternative: try /relay endpoint
        relay_body = {
            "type": "PROXY",
            "conditionId": CONDITION_ID,
            "indexSets": [1, 2],
        }
        result = relayer_request("POST", "/relay", relay_body)

if __name__ == "__main__":
    main()
