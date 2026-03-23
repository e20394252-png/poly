"""
Check the Shanghai position status and attempt to redeem if resolved.
Position is on proxy address 0x0411F017251a5918422FECc2cDeA558a0A5c6115
"""
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# 1. Get position details
proxy_addr = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"
print(f"Fetching positions for proxy addr {proxy_addr}...")
r = requests.get(f"https://data-api.polymarket.com/positions?user={proxy_addr}", timeout=10)
positions = r.json()

for p in positions:
    if float(p.get('size', 0)) > 0:
        print(f"\n=== POSITION DETAILS ===")
        print(json.dumps(p, indent=2))
        print(f"========================\n")
        
        condition_id = p.get('conditionId')
        token_id = p.get('asset')
        outcome = p.get('outcome')
        size = p.get('size')
        cur_price = p.get('curPrice')
        
        # 2. Check market status on Gamma
        print(f"Checking market status for conditionId={condition_id}...")
        mr = requests.get(f"https://gamma-api.polymarket.com/markets?condition_ids={condition_id}", timeout=10)
        markets = mr.json()
        if markets:
            market = markets[0]
            print(f"  Market: {market.get('question')}")
            print(f"  Active: {market.get('active')}")
            print(f"  Closed: {market.get('closed')}")
            print(f"  UMA Resolution: {market.get('umaResolutionStatus')}")
            print(f"  NegRisk: {market.get('negRisk')}")
            print(f"  Outcomes: {market.get('outcomes')}")
            print(f"  OutcomePrices: {market.get('outcomePrices')}")
            
            # 3. Check who holds the tokens
            print(f"\n  Checking token holder...")
            print(f"  Signer (EOA): 0xD57d3F5BB3A3a2ce4796F9B7b8a9f01F51150485")
            print(f"  Proxy wallet: {proxy_addr}")
            print(f"  The position is held by the PROXY wallet, not the signer.")
            print(f"  For redemption, the proxy wallet needs to call redeemPositions.")
            print(f"  Since we control the signer (EOA), we can use the Polymarket Relayer")
            print(f"  to relay the redemption transaction through the proxy wallet.")
