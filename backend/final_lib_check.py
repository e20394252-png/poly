import os
import requests
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType

load_dotenv()

host = "https://clob.polymarket.com"
key = os.getenv("API_KEY")
secret = os.getenv("API_SECRET")
passphrase = os.getenv("API_PASSPHRASE")
pk = os.getenv("PRIVATE_KEY")
proxy_url = os.getenv("PROXY_URL")

creds = ApiCreds(api_key=key, api_secret=secret, api_passphrase=passphrase)
client = ClobClient(host, key=pk, chain_id=POLYGON, creds=creds)

# Manual proxy from user/data-api
target_addr = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"

print(f"Checking Balance for: {target_addr}")
params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
try:
    # Most library methods don't take an address, they use the one from client
    # but let's see what the default is first
    res = client.get_balance_allowance(params)
    print(f"Default balance: {res}")
    
    # Check if we can get it for proxy explicitly if the lib supports it
    # (some versions allow it in params)
except Exception as e:
    print(f"Error: {e}")
