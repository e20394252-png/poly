import os
import requests
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ClobClientConfig
from py_clob_client.constants import POLYGON

load_dotenv()

host = "https://clob.polymarket.com"
key = os.getenv("API_KEY")
secret = os.getenv("API_SECRET")
passphrase = os.getenv("API_PASSPHRASE")
pk = os.getenv("PRIVATE_KEY")
proxy_url = os.getenv("PROXY_URL")

print(f"Initializing for PK: ...{pk[-4:]}")
print(f"Using Proxy: {proxy_url}")

# Setup httpx proxy patch if needed
if proxy_url:
    import httpx
    # Simplified patching for this script
    original_get = requests.get
    def proxied_get(*args, **kwargs):
        kwargs['proxies'] = {"http": proxy_url, "https": proxy_url}
        return original_get(*args, **kwargs)
    requests.get = proxied_get

client = ClobClient(
    host,
    key=key,
    secret=secret,
    passphrase=passphrase,
    funder=pk,
    chain_id=POLYGON
)

try:
    addr = client.get_address()
    print(f"Signer Address: {addr}")
    proxy = client.get_proxy_address()
    print(f"Polymarket Proxy Address: {proxy}")
except Exception as e:
    print(f"Error: {e}")
