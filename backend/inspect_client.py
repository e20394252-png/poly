import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

from py_clob_client.clob_types import ApiCreds
creds = ApiCreds(api_key=API_KEY, api_secret=API_SECRET, api_passphrase=API_PASSPHRASE)

client = ClobClient(
    host="https://clob.polymarket.com", 
    key=PRIVATE_KEY, 
    chain_id=137,
    creds=creds
)

from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
token_id = "78744428529323627966039202364573530792686585337019104425832097490638336271086"
print(f"Updating allowance for {token_id}...")
try:
    params = BalanceAllowanceParams(asset_type=AssetType.CONDITIONAL, token_id=token_id)
    res = client.update_balance_allowance(params)
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
