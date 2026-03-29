import os
import sys
import time
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
import threading
from typing import Any, List

# Fix Windows console encoding (cp1251 can't handle all Unicode chars)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"ERROR in init_client (setting proxy client): {e}", flush=True)
        pass

from py_clob_client.clob_types import (
    OrderArgs, 
    OrderType, 
    PartialCreateOrderOptions, 
    BalanceAllowanceParams, 
    AssetType
)
from py_clob_client.order_builder.constants import BUY, SELL

print("=== BOT STARTED ===", flush=True)



def _get_rpc_balance_internal(addr: str, rpc_url: str, proxies: dict = None) -> float:
    print(f"STEP: _get_rpc_balance_internal called for addr={addr}, rpc_url={rpc_url}", flush=True)
    if not addr:
        print("STEP: _get_rpc_balance_internal: addr is empty", flush=True)
        return 0

    tokens = ["0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"]
    total_bal = 0
    for token in tokens:
        try:
            data = "0x70a08231" + addr[2:].zfill(64)
            payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": token, "data": data}, "latest"], "id": 1}
            print(f"STEP: _get_rpc_balance_internal: Fetching balance for token={token}, payload={payload}", flush=True)
            response = requests.post(rpc_url, json=payload, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                try:
                    resp_json = response.json()
                    print(f"STEP: _get_rpc_balance_internal: Response for token={token}, JSON={resp_json}", flush=True)
                    if 'result' in resp_json and resp_json['result'] != '0x':
                        total_bal += int(resp_json['result'], 16) / 1e6
                except ValueError as json_err:
                    print(f"ERROR in _get_rpc_balance_internal (JSON decode) for {token}: {json_err} - raw response: {response.text[:200]}", flush=True)
            else:
                print(f"STEP: _get_rpc_balance_internal: Non-200 response for token={token}, status={response.status_code}", flush=True)
                
        except Exception as e:
            print(f"ERROR in _get_rpc_balance_internal for token {token}: {e}", flush=True)
    print(f"STEP: _get_rpc_balance_internal: Total balance for {addr} = {total_bal}", flush=True)
    return total_bal


# Load configuration
load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

def select_best_proxy():
    proxies_str = os.getenv("PROXIES_LIST")
    if not proxies_str:
        return os.getenv("PROXY_URL")
    
    import requests
    import time
    p_list = [p.strip() for p in proxies_str.split(',') if p.strip()]
    if not p_list:
        return os.getenv("PROXY_URL")
        
    print(f"Testing {len(p_list)} proxies from pool...")
    best_proxy = None
    best_time = float('inf')
    test_url = "https://clob.polymarket.com/time"
    
    for p in p_list:
        try:
            t0 = time.time()
            r = requests.get(test_url, proxies={'http': p, 'https': p}, timeout=10)
            t = time.time() - t0
            if r.status_code == 200 and t < best_time:
                best_time = t
                best_proxy = p
                print(f"  -> {p.split('@')[-1]} OK! ({t:.2f}s)")
        except Exception as e:
            print(f"ERROR in select_best_proxy: {e}", flush=True)
            print(f"  -> {p.split('@')[-1]} FAILED")
            pass
            
    if best_proxy:
        print(f"Selected fastest proxy: {best_proxy.split('@')[-1]} ({best_time:.2f}s)")
        return best_proxy
    print("Warning: All proxies failed. Using first proxy as fallback.")
    return p_list[0]

PROXY_URL = select_best_proxy()
RPC_URL = os.getenv("RPC_URL", "https://1rpc.io/matic")
USE_PROXY_WALLET = os.getenv("USE_PROXY_WALLET", "0").strip().lower() in ("1", "true", "yes", "y")

# Apply proxy globally for requests if PROXY_URL is provided
if PROXY_URL:
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL
    
    # Also patch the py-clob-client's internal httpx client
    import httpx
    try:
        from py_clob_client.http_helpers import helpers
        helpers._http_client = httpx.Client(proxy=PROXY_URL, timeout=httpx.Timeout(60.0))
        print(f"Patched py-clob-client with proxy config")
    except Exception as e:
        print(f"Warning: Failed to patch py-clob-client proxy: {e}")
else:
    print("No PROXY_URL set — connecting directly (recommended if not geo-blocked).")


# Settings
TRADE_AMOUNT_USDC = float(os.getenv("TRADE_AMOUNT_USDC", 1.0))
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", 15))

GAMMA_API_URL = "https://gamma-api.polymarket.com"

# Focus categories (e.g. "Politics,Crypto,Sports")
FOCUS_CATEGORIES = [c.strip() for c in os.getenv("FOCUS_CATEGORIES", "").split(',') if c.strip()]

class BotState:
    def __init__(self):
        self.status = "stopped"
        self.current_action = "System Initialized"
        self.latency_ms = 0
        self.active_proxy = PROXY_URL
        self.last_poll = None
        self.trades_count = 0
        self.balance = 0.0
        self.realized_profit = 0.0
        self.recent_trades = []
        self.opportunities = []
        self.positions = []
        self.proxy_address = None
        self.config = {
            "trade_amount": TRADE_AMOUNT_USDC,
            "poll_interval": POLL_INTERVAL_SECONDS,
            "take_profit_threshold": 0.025,   # 2.5% TP for high-frequency scalping
            "stop_loss_threshold": -0.08,     # -8% SL for strict risk control
            "price_min": 0.70,                # High probability zone floor
            "price_max": 0.89,                # High probability zone ceiling
            "max_positions": 10,               # Limit concurrent positions
            "max_hold_time_minutes": 30,       # Max hold time for positions
        }
        self.stop_event = threading.Event()
        self.logs = [] # NEW: Buffer for system logs
        self.address = None
        
        # Load persisted state on init
        self.load_state()

    def load_state(self):
        import json
        try:
            with open('bot_status_data.json', 'r') as f:
                data = json.load(f)
                self.trades_count = data.get('trades_count', 0)
                self.realized_profit = data.get('realized_profit', 0.0)
                self.recent_trades = data.get('recent_trades', [])
        except Exception:
            pass # File doesn't exist or is corrupted, start fresh

    def save_state(self):
        import json
        try:
            with open('bot_status_data.json', 'w') as f:
                json.dump({
                    "trades_count": self.trades_count,
                    "realized_profit": self.realized_profit,
                    "recent_trades": self.recent_trades
                }, f)
        except Exception as e:
            print(f"Error saving state to disk: {e}")

    def add_trade(self, trade):
        self.recent_trades.insert(0, trade)
        if len(self.recent_trades) > 50:
            self.recent_trades.pop()
        self.trades_count += 1
        self.save_state()

    def add_log(self, msg):
        """Adds a message to the system log buffer."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        print(log_entry) # Still print to stdout for Render
        self.logs.insert(0, log_entry)
        if len(self.logs) > 50:
            self.logs.pop()

global_state = BotState()

# Optional hardcoded proxy wallet (funder) to match Polymarket "proxy wallet".
# In EOA-only mode (default), we ignore proxy wallets to keep assets on the signer.
MANUAL_PROXY = os.getenv("MANUAL_PROXY")

global_state.proxy_address = MANUAL_PROXY

# Initialize CLOB Client in background to avoid blocking server start
client = None

def init_client():
    global_state.add_log("init_client function started.")
    global client
    global_state.add_log("Checking API credentials...")
    if all([PRIVATE_KEY, API_KEY, API_SECRET, API_PASSPHRASE]):
        try:
            # from py_clob_client.clob_types import ApiCreds, SignatureType # SignatureType is missing in 0.34.6
            from py_clob_client.clob_types import ApiCreds
            # Signature types (based on py-order-utils/model.py): EOA = 0, POLY_PROXY = 1, POLY_GNOSIS = 2
            EOA = 0
            POLY_PROXY = 1
            
            creds = ApiCreds(api_key=API_KEY, api_secret=API_SECRET, api_passphrase=API_PASSPHRASE)
            global_state.add_log("Initializing CLOB Client...")
            
            # Determine signature type and funder based on wallet mode
            if USE_PROXY_WALLET and global_state.proxy_address:
                # POLY_PROXY mode (Magic Link / Google login)
                signature_type = POLY_PROXY
                funder = global_state.proxy_address
                global_state.add_log(f"POLY_PROXY mode: funder={funder}")
            else:
                # EOA mode (standard wallet)
                signature_type = EOA
                import eth_account
                funder = eth_account.Account.from_key(PRIVATE_KEY).address
                global_state.add_log(f"EOA mode: funder={funder}")

            client = ClobClient(
                host="https://clob.polymarket.com", 
                key=PRIVATE_KEY, 
                chain_id=137,
                creds=creds,
                signature_type=signature_type,
                funder=funder,
            )
            global_state.add_log(f"ClobClient instance created: {client}")
            global_state.address = client.get_address()
            global_state.add_log(f"CLOB Client Initialized for Signer: {global_state.address}")
            global_state.add_log(f"Funder (Proxy Wallet): {funder}")
            
            # Trigger initial sync once client is ready
            global_state.add_log("Triggering initial balance and positions update...")
            update_balance_and_positions()
            
        except Exception as e:
            global_state.add_log(f"Failed to initialize CLOB Client: {e}")
            import traceback
            traceback.print_exc()
    else:
        global_state.add_log("API credentials are NOT complete.")
        global_state.add_log("Missing API Credentials in .env!")

threading.Thread(target=init_client, daemon=True).start()


def _fetch_gamma_market_by_condition_id(condition_id: str) -> dict[str, Any] | None:
    """
    Fetch a single market object from Gamma by conditionId.
    Gamma expects `condition_ids` as a query param.
    """
    try:
        proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
        url = f"{GAMMA_API_URL}/markets?condition_ids={condition_id}"
        r = requests.get(url, proxies={"http": None, "https": None}, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        if isinstance(data, list) and data:
            return data[0]
        return None
    except Exception as e:
        print(f"ERROR in filter_short_term_opportunities: {e}", flush=True)
        return None


def redeem_resolved_position(pos: dict[str, Any]) -> dict[str, Any]:
    """
    Redeem resolved Conditional Tokens into collateral (USDC.e) via the
    ConditionalTokens contract on Polygon.

    Important: redemption burns tokens held by `msg.sender`. If the position
    is held in a Polymarket proxy wallet, you must redeem from that wallet.
    This implementation can only sign for the EOA (PRIVATE_KEY).
    """
    if not client:
        return {"ok": False, "error": "CLOB Client not initialized"}
    if not PRIVATE_KEY:
        return {"ok": False, "error": "Missing PRIVATE_KEY"}

    condition_id = pos.get("market_id") or pos.get("conditionId") or pos.get("condition_id")
    outcome = pos.get("outcome")
    token_id = pos.get("token_id")
    if not condition_id or not outcome or not token_id:
        return {"ok": False, "error": "Position missing conditionId/outcome/token_id"}

    market = _fetch_gamma_market_by_condition_id(condition_id)
    if not market:
        return {"ok": False, "error": "Failed to fetch market from Gamma"}

    # If orders are not accepted and market is closed, redemption is the right path.
    uma_status = market.get("umaResolutionStatus")
    if uma_status not in ("resolved", "proposed"):
        # keep it permissive; some markets settle after proposed, but at least surface status
        pass

    import json as _json
    outcomes = _json.loads(market.get("outcomes", "[]")) if isinstance(market.get("outcomes"), str) else market.get("outcomes", [])
    if not isinstance(outcomes, list) or not outcomes:
        return {"ok": False, "error": "Market outcomes not available"}

    try:
        outcome_index = outcomes.index(outcome)
    except ValueError:
        # Sometimes Data API uses "YES/NO" capitalization
        normalized = {str(o).strip().lower(): i for i, o in enumerate(outcomes)}
        key = str(outcome).strip().lower()
        if key in normalized:
            outcome_index = normalized[key]
        else:
            return {"ok": False, "error": f"Outcome '{outcome}' not found in market outcomes {outcomes}"}

    # indexSet is a bitmask: 1 << outcome_index
    index_set = 1 << int(outcome_index)

    # On-chain call: ConditionalTokens.redeemPositions(collateralToken, parentCollectionId, conditionId, indexSets)
    # ConditionalTokens contract address comes from SDK config.
    conditional_tokens_addr = client.get_conditional_address()
    from py_clob_client.config import get_contract_config
    collateral_addr = get_contract_config(137, neg_risk=bool(market.get("negRisk", False))).collateral

    # Minimal ABI for redeemPositions
    conditional_tokens_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "collateralToken", "type": "address"},
                {"internalType": "bytes32", "name": "parentCollectionId", "type": "bytes32"},
                {"internalType": "bytes32", "name": "conditionId", "type": "bytes32"},
                {"internalType": "uint256[]", "name": "indexSets", "type": "uint256[]"},
            ],
            "name": "redeemPositions",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]

    # Use Web3 for signing the tx
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"proxies": {"http": None, "https": None}, "timeout": 10}))
    if not w3.is_connected():
        return {"ok": False, "error": f"RPC not reachable: {RPC_URL}"}

    acct = w3.eth.account.from_key(PRIVATE_KEY)
    signer_addr = acct.address

    # If the position is likely held in proxy wallet, warn early.
    holder_addr = global_state.proxy_address or global_state.address
    if holder_addr and holder_addr.lower() != signer_addr.lower():
        return {
            "ok": False,
            "error": "Position is held in proxy wallet; redemption requires proxy wallet signing/execution",
            "signer": signer_addr,
            "holder": holder_addr,
        }

    contract = w3.eth.contract(address=w3.to_checksum_address(conditional_tokens_addr), abi=conditional_tokens_abi)
    parent_collection_id = "0x" + "00" * 32

    try:
        nonce = w3.eth.get_transaction_count(signer_addr)
        tx = contract.functions.redeemPositions(
            w3.to_checksum_address(collateral_addr),
            parent_collection_id,
            condition_id,
            [index_set],
        ).build_transaction(
            {
                "from": signer_addr,
                "nonce": nonce,
                "chainId": 137,
            }
        )
        # Basic gas fill
        tx.setdefault("gasPrice", w3.eth.gas_price)
        tx.setdefault("gas", int(w3.eth.estimate_gas(tx) * 1.2))

        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return {"ok": True, "tx_hash": tx_hash.hex(), "condition_id": condition_id, "outcome": outcome, "index_set": index_set}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_active_events():
    global_state.add_log("Entering fetch_active_events...")
    """Fetches active events from the Gamma API."""
    print("STEP: Entering fetch_active_events", flush=True)
    global_state.current_action = "Fetching Active Markets from Polymarket..."
    try:
        all_events = []
        # Sort by volume DESC to get the most liquid (and active) ones first
        url = f"{GAMMA_API_URL}/events?active=true&closed=false&order=volume&ascending=false&limit=1000"
        global_state.add_log(f"Fetching active events from Gamma API (Sorted by volume)...")
        
        # We fetch in one big chunk of 1000 now that we have sorting
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            all_events = response.json()
            global_state.add_log(f"Total active events fetched: {len(all_events)}")
        
        print(f"STEP: Fetched {len(all_events)} active events", flush=True)
        return all_events
    except Exception as e:
        global_state.add_log(f"Error fetching events: {e}")
        return []

def filter_short_term_opportunities(events: List[dict]) -> List[dict]:
    print("STEP: Entering filter_short_term_opportunities", flush=True)
    global_state.current_action = "Filtering short-term opportunities..."
    """Filters events that close soon (Widened to 7 days)"""
    opportunities = []
    now = datetime.now(timezone.utc)
    
    # STRATEGY: Volatility Scalping — scan 3-day window for immediate/short-lived markets
    min_time = now + timedelta(minutes=1)
    max_time = now + timedelta(days=3)
    
    for event in events:
        try:
            end_date_str = event.get('endDate')
            if not end_date_str:
                global_state.add_log(f"DEBUG: Event '{event.get('title', 'N/A')}' filtered - no endDate.")
                continue

            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

            # Category Filtering
            if FOCUS_CATEGORIES:
                event_tags = [t.get('label', '').lower() for t in event.get('tags', []) if isinstance(t, dict)]
                if not any(cat.lower() in event_tags for cat in FOCUS_CATEGORIES):
                    global_state.add_log(f"DEBUG: Event '{event.get('title', 'N/A')}' filtered - category mismatch. Tags: {event_tags}, Focus: {FOCUS_CATEGORIES}")
                    continue

            if not (min_time <= end_date <= max_time):
                global_state.add_log(f"DEBUG: Event '{event.get('title', 'N/A')}' filtered - outside time window ({end_date}). Min: {min_time}, Max: {max_time}")
                continue

            opportunities.append(event)
        except Exception as e:
            print(f"ERROR in filter_short_term_opportunities loop: {e}", flush=True)
            continue
            
    global_state.add_log(f"Filtered {len(opportunities)} events from {len(events)} total active events.")
    print(f"STEP: Found {len(opportunities)} short-term opportunities", flush=True)
    return opportunities

def analyze_and_trade(opportunities, placed_trades):
    print("STEP: Entering analyze_and_trade", flush=True)
    global_state.add_log(f"Entering analyze_and_trade with {len(opportunities)} opportunities and {len(placed_trades)} placed trades.")
    """Analyzes markets within the events and decides on trades."""
    import json
    from py_clob_client.order_builder.constants import BUY
    
    global_state.current_action = "Analyzing Markets for Alpha..."
    global_state.opportunities = []
    
    if not opportunities:
        print(f"[{datetime.now().isoformat()}] No short-term opportunities found right now.")
        return
        
    print(f"=====================================")
    print(f"[{datetime.now().isoformat()}] Found {len(opportunities)} impending events.")
    
    total_markets_scanned = 0
    opportunities_found = 0

    for event in opportunities:
        # print(f"\nAnalyzing Event: {event.get('title')}")
        # print(f"Closes at: {event.get('endDate')}")
        
        markets = event.get('markets', [])
        for market in markets:
            total_markets_scanned += 1
            if not market.get('active') or market.get('closed'):
                global_state.add_log(f"DEBUG: Market '{question}' filtered - not active or closed.")
                continue
            
            question = market.get('question')
            outcomes = json.loads(market.get('outcomes', '[]'))
            outcome_prices = json.loads(market.get('outcomePrices', '[]'))
            clob_token_ids = json.loads(market.get('clobTokenIds', '[]'))
            tick_size = str(market.get('orderPriceMinTickSize', '0.01'))
            neg_risk = market.get('negRisk', False)
            try:
                tick_f = float(tick_size)
            except (ValueError, TypeError):
                tick_f = 0.01
            
            if len(outcomes) != len(outcome_prices) or len(outcomes) != len(clob_token_ids):
                global_state.add_log(f"DEBUG: Market {question}: Mismatch in outcomes, prices or token IDs. Skipping.")
                print(f"[{datetime.now().isoformat()}]  -> Market {question}: Mismatch in outcomes, prices or token IDs. Skipping.")
                continue
                
            print(f"[{datetime.now().isoformat()}]  -> Market: {question}")
            for i in range(len(outcomes)):
                outcome = outcomes[i]
                price_str = outcome_prices[i]
                token_id = clob_token_ids[i]
                
                if token_id in placed_trades:
                    global_state.add_log(f"DEBUG: Outcome '{outcome}' for market '{question}' already traded. Skipping.")
                    print(f"[{datetime.now().isoformat()}]      - Outcome '{outcome}': Already traded. Skipping.")
                    continue
                
                try:
                    price_f = float(price_str)
                except (ValueError, TypeError):
                    global_state.add_log(f"DEBUG: Outcome '{outcome}' for market '{question}': Invalid price format '{price_str}'. Skipping.")
                    print(f"[{datetime.now().isoformat()}]      - Outcome '{outcome}': Invalid price format '{price_str}'. Skipping.")
                    continue

                # Clamp to valid price range for this market.
                # The SDK enforces max price = 1 - tick_size.
                max_price = 1.0 - tick_f
                if price_f > max_price:
                    price_f = max_price

                # STRATEGY: High-Frequency Momentum Scalping — buy in the 70%-89% range
                # High probability but still room for small profitable movements
                price_min = global_state.config.get('price_min', 0.70)
                price_max = global_state.config.get('price_max', 0.89)
                
                if price_f >= price_min and price_f <= price_max:
                    # Add to current opportunities for dashboard
                    global_state.opportunities.append({
                        "event_title": event.get('title'),
                        "market_question": question,
                        "outcome": outcome,
                        "price": price_f,
                        "token_id": token_id
                    })
                    
                    opportunities_found += 1
                    
                    # Check position limit
                    max_positions = global_state.config.get('max_positions', 10)
                    if len(global_state.positions) >= max_positions:
                        if opportunities_found == 1: # Only log this once per scan cycle
                            global_state.add_log(f"DEBUG: Max positions reached ({max_positions}). Skipping new trades.")
                        continue
                        
                    print(f"[{datetime.now().isoformat()}]      [!] HIGH-FREQUENCY SCALP OPPORTUNITY: '{outcome}' @ ${price_f:.2f}")
                    
                    if client is None:
                        global_state.add_log(f"DEBUG: Cannot place order for '{outcome}' - CLOB Client is not initialized.")
                        print(f"[{datetime.now().isoformat()}]          -> Cannot place order: CLOB Client is not initialized.")
                        continue
                        
                    # Calculate shares based on stake in USDC with position sizing adjustment
                    # `py-clob-client` expects `size` in conditional token units (shares), not USDC.
                    min_size = float(market.get("orderMinSize", 1) or 1)
                    
                    # Dynamic position sizing based on confidence (higher price = smaller position)
                    confidence_multiplier = 1.0 - (price_f - price_min) / (price_max - price_min)
                    adjusted_trade_amount = TRADE_AMOUNT_USDC * (0.7 + 0.3 * confidence_multiplier)
                    
                    shares = round(adjusted_trade_amount / price_f, 2) if price_f > 0 else 0.0
                    if shares < min_size:
                        # If stake is too small for the market, bump to minimum size.
                        shares = min_size
                    cost_est = shares * price_f
                        
                    print(
                        f"[{datetime.now().isoformat()}]          -> Attempting to place order: BUY {shares} shares of '{outcome}' "
                        f"at ${price_f:.3f} (est. cost ${cost_est:.2f}, confidence: {confidence_multiplier:.2f})"
                    )
                    
                    try:
                        # Ensure collateral (USDC) allowance/balance is up to date before BUY.
                        try:
                            client.update_balance_allowance(
                                BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
                            )
                        except Exception as allow_err:
                            print(f"[{datetime.now().isoformat()}]          -> Warning: collateral allowance update failed: {allow_err}")

                        # Place Limit Order
                        response = client.create_and_post_order(
                            OrderArgs(
                                token_id=token_id,
                                price=price_f,
                                size=shares,
                                side=BUY,
                            ),
                            options=PartialCreateOrderOptions(
                                tick_size=tick_size,
                                neg_risk=neg_risk,
                            )
                        )
                        print(f"[{datetime.now().isoformat()}]          -> Order Success! ID: {response.get('orderID')}, Status: {response.get('status')}")
                        placed_trades.add(token_id)
                        
                        # Add to active positions for Take Profit tracking
                        global_state.positions.append({
                            "token_id": token_id,
                            "market_id": event.get('id'),
                            "title": event.get('title'),
                            "outcome": outcome,
                            "entry_price": price_f,
                            "shares": shares,
                            "entry_timestamp": datetime.now().isoformat()
                        })
                        
                        global_state.add_trade({
                            "timestamp": datetime.now().isoformat(),
                            "title": event.get('title'),
                            "market": question,
                            "outcome": outcome,
                            "price": price_f,
                            "size": shares,
                            "status": "success",
                            "order_id": response.get('orderID')
                        })
                    except Exception as e:
                        print(f"[{datetime.now().isoformat()}]          -> Order Failed: {e}")
                        global_state.add_log(f"DEBUG: Order for '{outcome}' failed: {e}")
                        global_state.add_trade({
                            "timestamp": datetime.now().isoformat(),
                            "title": event.get('title'),
                            "market": question,
                            "outcome": outcome,
                            "price": price_f,
                            "size": shares,
                            "status": "failed",
                            "error": str(e)
                        })
                            
                else:
                    global_state.add_log(f"DEBUG: Outcome '{outcome}' for market '{question}': price ${price_f:.2f} outside scalp range [{price_min:.2f}, {price_max:.2f}].")
                    print(f"[{datetime.now().isoformat()}]      - Outcome '{outcome}': ${price_f:.2f} (Outside volatility zone)")
    
    print(f"[{datetime.now().isoformat()}] Analysis Complete: Scanned {total_markets_scanned} markets, found {opportunities_found} opportunities.")
    print(f"=====================================")
    print("STEP: Exiting analyze_and_trade", flush=True)
    global_state.add_log("Finished analyzing and trading.")
            
def update_balance_and_positions():
    """Fetches current USDC balance and active positions from Polymarket."""
    global_state.current_action = "Syncing Balances & Active Positions..."
    print(f"[{datetime.now().isoformat()}] Starting balance update...")
    if not client:
        print("Error: CLOB Client not initialized")
        return

    try:
        # 1. Build new state locally to avoid state flickering on dashboard
        new_positions = []
        found_token_ids = set()
        any_positions_fetch_succeeded = False
        
        # 2. Fetch USDC Balance
        # Use RPC to check the actual wallet holding funds
        # NOTE: RPC calls go DIRECTLY (no proxy) — Polygon RPC is not geo-blocked
        if USE_PROXY_WALLET and global_state.proxy_address:
            # Check proxy wallet balance via RPC first (regular ERC20)
            try:
                rpc_url = RPC_URL or "https://1rpc.io/matic"
                proxies = {"http": None, "https": None}
                global_state.balance = _get_rpc_balance_internal(global_state.proxy_address, rpc_url, proxies)
                print(f"[{datetime.now().isoformat()}] Balance (proxy wallet): ${global_state.balance:.2f}")

                # If RPC balance is 0, try falling back to Data API
                if global_state.balance == 0:
                    try:
                        url = f"https://data-api.polymarket.com/value?user={global_state.proxy_address}"
                        response = requests.get(url, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            portfolio_value = 0
                            if isinstance(data, list) and len(data) > 0:
                                portfolio_value = float(data[-1].get('value', 0)) if isinstance(data[-1], dict) else 0
                            elif isinstance(data, dict):
                                portfolio_value = float(data.get('value', 0))
                            
                            global_state.balance = portfolio_value
                            print(f"[{datetime.now().isoformat()}] Balance from Data API (fallback): ${global_state.balance:.2f}")
                    except Exception as e2:
                        print(f"[{datetime.now().isoformat()}] Data API fallback failed: {e2}")
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] Error fetching proxy wallet balance: {e}")



        else:
            # EOA mode: use RPC
            try:
                rpc_url = RPC_URL or "https://1rpc.io/matic"
                proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
                global_state.balance = _get_rpc_balance_internal(global_state.address, rpc_url, proxies)
                print(f"[{datetime.now().isoformat()}] Balance from RPC (EOA mode): ${global_state.balance:.2f}")
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] Error fetching EOA balance from RPC: {e}")
                pass

        # 3. Fetch All Positions from Data API
        addresses_to_check = [global_state.proxy_address] if USE_PROXY_WALLET and global_state.proxy_address else [global_state.address]
            
        for addr in addresses_to_check:
            if not addr: continue
            try:
                url = f"https://data-api.polymarket.com/positions?user={addr}"
                proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
                response = requests.get(url, proxies=proxies, timeout=30)
                
                if response.status_code == 200:
                    any_positions_fetch_succeeded = True
                    data = response.json()
                    # Build lookup of existing timestamps to preserve them
                    existing_timestamps = {p['token_id']: p['entry_timestamp'] for p in global_state.positions}
                    for pos in data:
                        size = float(pos.get('size', 0))
                        token_id = pos.get('asset')
                        if size > 0 and token_id and token_id not in found_token_ids:
                            print(f"Found position: {pos.get('title')} ({size} shares)")
                            # FIX: Preserve original entry_timestamp — don't let it shift every poll
                            original_ts = existing_timestamps.get(token_id, datetime.now().isoformat())
                            new_positions.append({
                                "token_id": token_id,
                                "market_id": pos.get('conditionId'),
                                "title": pos.get('title', 'Existing Position'),
                                "outcome": pos.get('outcome', 'YES'),
                                "entry_price": float(pos.get('avgPrice', 0.5)),
                                "shares": size,
                                "current_price": float(pos.get('curPrice', 0.5)),
                                "pnl_percent": float(pos.get('percentPnl', 0)),
                                "entry_timestamp": original_ts
                            })
                            found_token_ids.add(token_id)
            except Exception as e:
                print(f"Error fetching positions for {addr}: {e}")
        
        # 4. Atomic swap (don't wipe positions if Data API is down)
        if any_positions_fetch_succeeded:
            global_state.positions = new_positions
        elif not global_state.positions and new_positions:
            # Defensive fallback: only set if we previously had none
            global_state.positions = new_positions
        else:
            print("Warning: Data API positions fetch failed; keeping last known positions.")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] An unexpected error occurred during balance/position update: {e}")

        print(f"[{datetime.now().isoformat()}] Fetched {len(new_positions)} positions.")
        global_state.last_poll = datetime.now().isoformat()
                
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error updating balance and positions: {e}")

def monitor_take_profit():
    """Checks active positions and sells if they are in profit."""
    if not client or not global_state.positions:
        return
    
    global_state.current_action = "Monitoring Active Positions for Take Profit..."
    print(f"Monitoring {len(global_state.positions)} active positions for Take Profit...")
    
    remaining_positions = []
    for pos in global_state.positions:
        try:
            # 1. Get current market price and liquidity
            current_price = 0.0
            best_bid = 0.0
            try:
                # Get orderbook to see real liquidity (may not exist for some tokens)
                try:
                    ob = client.get_order_book(pos['token_id'])
                    if hasattr(ob, 'bids') and ob.bids:
                        best_bid = float(ob.bids[0].price)
                    elif isinstance(ob, dict) and 'bids' in ob and ob['bids']:
                        # Handle both list of dicts and list of objects
                        first_bid = ob['bids'][0]
                        best_bid = float(first_bid.price if hasattr(first_bid, 'price') else first_bid.get('price', 0))
                except Exception as ob_err:
                    # Don't abort TP just because orderbook endpoint is missing/empty (404 etc.)
                    print(f"     -> No orderbook for token {pos.get('token_id')}: {ob_err}")
                
                # Use midpoint as a fallback/reference
                try:
                    price_info = client.get_midpoint(pos['token_id'])
                    current_price = float(price_info.get('midpoint', 0))
                except Exception as mp_err:
                    print(f"     -> Midpoint unavailable for {pos.get('token_id')}: {mp_err}")
                
                # Fallback to last trade price if midpoint is 0
                if current_price == 0:
                    try:
                        last_trade = client.get_last_trade_price(pos['token_id'])
                        current_price = float(last_trade.get('price', 0))
                    except Exception as e:
                        print(f"ERROR in monitor_take_profit (last_trade_price): {e}", flush=True)

                # Final fallback to price from Data API (stored in position)
                if current_price == 0:
                    current_price = pos.get('current_price', 0)
                
                if best_bid > 0:
                    # If we have a real bid, we use it as the "real" price we can get
                    current_price = best_bid
                
                print(f"     -> Prices for {pos['title']}: Bid: {best_bid} | Mid/Last: {current_price}")
            except Exception as e:
                print(f"     -> Error fetching price for {pos['title']}: {e}")
                import traceback
                traceback.print_exc()
                continue 
            
            # 2. Check profit threshold, stop-loss, max hold time, or near-expiry exit
            tp = global_state.config.get('take_profit_threshold', 0.025)
            sl = global_state.config.get('stop_loss_threshold', -0.08)
            max_hold_minutes = global_state.config.get('max_hold_time_minutes', 30)
            
            # Calculate time held
            entry_time = datetime.fromisoformat(pos['entry_time'].replace('Z', '+00:00'))
            hold_time_minutes = (datetime.now(timezone.utc) - entry_time).total_seconds() / 60
            
            is_huge_profit = current_price > pos['entry_price'] * 2.0
            is_near_max = current_price >= 0.98
            is_target_hit = current_price > pos['entry_price'] * (1 + tp)
            is_stop_loss = pos['entry_price'] > 0 and (current_price - pos['entry_price']) / pos['entry_price'] < sl
            is_max_hold_time = hold_time_minutes > max_hold_minutes

            if is_huge_profit or is_near_max or is_target_hit or is_stop_loss or is_max_hold_time:
                if is_max_hold_time:
                    reason = f"MAX HOLD TIME ({hold_time_minutes:.1f} min)"
                elif is_stop_loss:
                    reason = "STOP LOSS"
                elif is_huge_profit:
                    reason = "HUGE PROFIT"
                elif is_near_max:
                    reason = "MAX REACHED"
                else:
                    reason = "TARGET HIT"
                    
                print(f" [!] TAKE PROFIT TRIGGERED ({reason}) for {pos['title']} ({pos['outcome']})")
                print(f"     Entry: {pos['entry_price']} | Current/Bid: {current_price} | ROI: {((current_price/pos['entry_price'])-1)*100:.1f}% | Hold: {hold_time_minutes:.1f}min")
                
                # 3. Execute Sell Order
                try:
                    # ENSURE ALLOWANCE for the token
                    print(f"     -> Ensuring allowance for {pos['token_id']}...")
                    try:
                        allowance_params = BalanceAllowanceParams(
                            asset_type=AssetType.CONDITIONAL,
                            token_id=pos['token_id']
                        )
                        client.update_balance_allowance(allowance_params)
                    except Exception as allow_err:
                        print(f"     -> Allowance check failed, proceeding anyway (expected for proxy wallets): {allow_err}")
                    
                    # Place a sell order slightly below current bid to ensure it hits or use the best bid exactly
                    sell_price = round(current_price * 0.995, 3) # 0.5% discount to ensure fill
                    if sell_price < 0.01: sell_price = 0.01
                    
                    print(f"     -> Attempting SELL at ${sell_price}")
                    order_args = OrderArgs(
                        price=sell_price,
                        size=round(pos['shares'], 2),
                        side=SELL,
                        token_id=pos['token_id']
                    )
                    res = client.create_and_post_order(order_args)
                    print(f"     -> Sell Order Posted: {res}")
                    
                    # Update realized profit estimate
                    profit = (sell_price - pos['entry_price']) * pos['shares']
                    global_state.realized_profit += profit
                    
                    global_state.add_trade({
                        "timestamp": datetime.now().isoformat(),
                        "title": pos['title'],
                        "market": f"EXIT ({reason})",
                        "outcome": "SELL",
                        "price": sell_price,
                        "size": sell_price * pos['shares'],
                        "status": "success",
                        "order_id": str(res.get('orderID')) if isinstance(res, dict) else "TP_EXIT"
                    })
                    continue # Successfully queued/executed, remove from tracking
                except Exception as sell_err:
                    print(f"     -> Sell Failed: {sell_err}")

            remaining_positions.append(pos)
        except Exception as e:
            print(f"Error in TP monitor: {e}")
            remaining_positions.append(pos)
            
    global_state.positions = remaining_positions

def run_bot_loop():
    """Main trading loop."""
    print(f"\nStarting Polymarket Trading Bot")
    global_state.add_log("Bot main loop started.")
    print(f"Trade Size: ${TRADE_AMOUNT_USDC} USDC | Poll Interval: {POLL_INTERVAL_SECONDS}s\n")
    
    # Seed placed_trades from current positions so we don't double-buy on restart
    placed_trades = set(pos['token_id'] for pos in global_state.positions)
    
    global_state.status = "running"
    global_state.stop_event.clear()
    while not global_state.stop_event.is_set() and global_state.status == "running":
        try:
            global_state.last_poll = datetime.now().isoformat()
            
            # Measure API Latency
            global PROXY_URL
            try:
                t0 = time.time()
                requests.get("https://clob.polymarket.com/time", proxies={"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None, timeout=5)
                global_state.latency_ms = int((time.time() - t0) * 1000)
            except Exception as e:
                print(f"ERROR in run_bot_loop (proxy latency check): {e}", flush=True)
                global_state.latency_ms = -1
                
            # Auto-rotate proxy if latency is terrible (>2000ms) or failed
            if global_state.latency_ms > 2000 or global_state.latency_ms == -1:
                print(f"[{datetime.now().isoformat()}] Latency {global_state.latency_ms}ms is unacceptable. Rotating proxy...")
                global_state.current_action = "Rotating proxy due to high latency..."
                new_proxy = select_best_proxy()
                if new_proxy and new_proxy != PROXY_URL:
                    PROXY_URL = new_proxy
                    global_state.active_proxy = PROXY_URL
                    os.environ['HTTP_PROXY'] = PROXY_URL
                    os.environ['HTTPS_PROXY'] = PROXY_URL
                    import httpx
                    try:
                        from py_clob_client.http_helpers import helpers
                        helpers._http_client = httpx.Client(proxy=PROXY_URL, timeout=httpx.Timeout(60.0))
                    except Exception as e:
                        print(f"ERROR in run_bot_loop (py_clob_client.http_helpers): {e}", flush=True)
            
            print("STEP: Before update_balance_and_positions", flush=True)
            # Update analytics
            update_balance_and_positions()
            print("STEP: After update_balance_and_positions", flush=True)
            monitor_take_profit()
            print("STEP: After monitor_take_profit", flush=True)
            events = fetch_active_events()
            print("STEP: After fetch_active_events", flush=True)
            short_term = filter_short_term_opportunities(events)
            print("STEP: After filter_short_term_opportunities", flush=True)
            analyze_and_trade(short_term, placed_trades)
            print("STEP: After analyze_and_trade", flush=True)
            
            global_state.current_action = f"Sleeping for {POLL_INTERVAL_SECONDS}s..."
            print(f"\nWaiting {POLL_INTERVAL_SECONDS} seconds...")
            time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"Critical Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(30)
    global_state.status = "stopped"

if __name__ == "__main__":
    # Keep bot alive
    while not global_state.stop_event.is_set():
        try:
            run_bot_loop()
        except Exception as e:
            import traceback
            global_state.add_log(f"Critical Error in main loop: {e}")
            traceback.print_exc()
            
        time.sleep(POLL_INTERVAL_SECONDS)

