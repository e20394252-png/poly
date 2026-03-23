"""Test CLOB API WITHOUT proxy"""
import os
from dotenv import load_dotenv
load_dotenv()

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

pk = os.getenv("PRIVATE_KEY")

creds = ApiCreds(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    api_passphrase=os.getenv("API_PASSPHRASE"),
)

# NO proxy patching at all
print("Initializing ClobClient WITHOUT proxy...")
client = ClobClient(
    host="https://clob.polymarket.com",
    key=pk,
    chain_id=137,
    creds=creds,
    signature_type=0,
)

print(f"Signer: {client.get_address()}")

try:
    ok = client.get_ok()
    print(f"Server OK: {ok}")
except Exception as e:
    print(f"Server OK failed: {e}")

# Try get_api_keys to confirm L2 auth works
try:
    keys = client.get_api_keys()
    print(f"API Keys: {keys}")
except Exception as e:
    print(f"get_api_keys failed: {e}")

# Try Data API without proxy
import requests
addr = client.get_address()
proxy_addr = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"

print(f"\nData API (no proxy) - signer {addr}:")
try:
    r = requests.get(f"https://data-api.polymarket.com/positions?user={addr}", timeout=10)
    data = r.json()
    print(f"  Found {len(data)} positions")
    for p in data:
        if float(p.get('size', 0)) > 0:
            print(f"  -> {p.get('title')}: {p.get('size')} shares, outcome={p.get('outcome')}, curPrice={p.get('curPrice')}")
except Exception as e:
    print(f"  Failed: {e}")

print(f"\nData API (no proxy) - proxy addr {proxy_addr}:")
try:
    r = requests.get(f"https://data-api.polymarket.com/positions?user={proxy_addr}", timeout=10)
    data = r.json()
    print(f"  Found {len(data)} positions")
    for p in data:
        if float(p.get('size', 0)) > 0:
            print(f"  -> {p.get('title')}: {p.get('size')} shares, outcome={p.get('outcome')}, curPrice={p.get('curPrice')}, token={p.get('asset')}")
except Exception as e:
    print(f"  Failed: {e}")
