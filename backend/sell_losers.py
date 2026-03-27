import os
import time
import requests
from dotenv import load_dotenv

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, OrderType, BalanceAllowanceParams, AssetType, PartialCreateOrderOptions
from py_clob_client.order_builder.constants import SELL

# Fix Windows console encoding
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

PROXY_URL = os.getenv('PROXY_URL')
import httpx
try:
    from py_clob_client.http_helpers import helpers
    from py_clob_client.constants import POLYGON
    if PROXY_URL:
        helpers._http_client = httpx.Client(proxy=PROXY_URL, timeout=httpx.Timeout(60.0))
        print(f"Patched py-clob-client with proxy config")
except Exception as e:
    print(f"Failed to patch proxy: {e}")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")
USE_PROXY_WALLET = os.getenv("USE_PROXY_WALLET", "0").strip().lower() in ("1", "true", "yes", "y")
MANUAL_PROXY = os.getenv("MANUAL_PROXY")

try:
    creds = ApiCreds(api_key=API_KEY, api_secret=API_SECRET, api_passphrase=API_PASSPHRASE)
    
    if USE_PROXY_WALLET and MANUAL_PROXY:
        signature_type = 1
        funder = MANUAL_PROXY
    else:
        signature_type = 0
        import eth_account
        funder = eth_account.Account.from_key(PRIVATE_KEY).address

    client = ClobClient(
        host="https://clob.polymarket.com", 
        key=PRIVATE_KEY, 
        chain_id=137,
        creds=creds,
        signature_type=signature_type,
        funder=funder,
    )
    my_addr = MANUAL_PROXY if (USE_PROXY_WALLET and MANUAL_PROXY) else client.get_address()
    print(f"Client initialised. Funder/Address: {my_addr}")

    url = f"https://data-api.polymarket.com/positions?user={my_addr}"
    response = requests.get(url, timeout=30)
    positions = response.json()
    
    sold_count = 0
    print(f"Found {len(positions)} positions.")
    for pos in positions:
        size = float(pos.get('size', 0))
        token_id = pos.get('asset')
        cur_price = float(pos.get('curPrice', 0))
        entry_price = float(pos.get('avgPrice', 0))
        title = pos.get('title', 'Unknown')
        
        # We target positions with current price less than 0.75 (definitely not part of the 85%+ strategy)
        if size > 0 and token_id and cur_price < 0.75:
            print(f"Attempting to sell: '{title}' | Size: {size} | CurPrice: {cur_price} | EntryPrice: {entry_price}")
            
            try:
                # Default values
                tick_size = "0.01" 
                neg_risk = False
                
                # Fetch market to get real tick_size and neg_risk
                market_url = f"https://gamma-api.polymarket.com/markets?condition_ids={pos.get('conditionId')}"
                mr = requests.get(market_url, timeout=10)
                if mr.status_code == 200:
                    market_data = mr.json()
                    if market_data and isinstance(market_data, list) and len(market_data) > 0:
                        tick_size = str(market_data[0].get('orderPriceMinTickSize', '0.01'))
                        neg_risk = market_data[0].get('negRisk', False)

                # Ensure allowance
                client.update_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.CONDITIONAL, token_id=token_id))

                # Aggressive sell order to ensure fill
                best_sell_price = max(float(tick_size), cur_price - 0.05)
                sell_price = round(best_sell_price, 3) if tick_size == "0.001" else round(best_sell_price, 2)
                
                print(f"  -> Placing order at {sell_price}")
                resp = client.create_and_post_order(
                    OrderArgs(
                        token_id=token_id,
                        price=sell_price,
                        size=size,
                        side=SELL,
                    ),
                    options=PartialCreateOrderOptions(tick_size=tick_size, neg_risk=neg_risk)
                )
                print(f"  -> Sold! Response: {resp.get('status')} {resp.get('success')}")
                sold_count += 1
                time.sleep(1) # ratelimit buffer
            except Exception as trade_e:
                print(f"  -> Failed to sell {title}: {trade_e}")
                import traceback
                traceback.print_exc()
                
    print(f"Finished executing sell-offs. Sold {sold_count} garbage positions.")

except Exception as e:
    print(f"Critical Error: {e}")
