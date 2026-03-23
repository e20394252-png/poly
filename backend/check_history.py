import os
import requests
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import ApiCreds

load_dotenv()

host = "https://clob.polymarket.com"
key = os.getenv("API_KEY")
secret = os.getenv("API_SECRET")
passphrase = os.getenv("API_PASSPHRASE")
pk = os.getenv("PRIVATE_KEY")
proxy_url = os.getenv("PROXY_URL")

creds = ApiCreds(api_key=key, api_secret=secret, api_passphrase=passphrase)
client = ClobClient(host, key=pk, chain_id=POLYGON, creds=creds)

print(f"Checking history for signer: {client.get_address()}")
try:
    # Try to fetch trades
    url = f"{host}/trades?maker_address={client.get_address()}"
    res = requests.get(url, timeout=5)
    print(f"Trades Status: {res.status_code}")
    if res.status_code == 200:
        print(f"Trades Data: {res.text[:500]}...")
        
    # Also try to fetch orders
    # NO specific endpoint for 'all orders' without market? Let's try some common ones
except Exception as e:
    print(f"Error: {e}")
