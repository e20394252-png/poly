import requests
import json

def get_token_balance(rpc_url, token_address, user_address):
    data = "0x70a08231" + user_address[2:].zfill(64)
    payload = {
        "jsonrpc": "2.0", "method": "eth_call",
        "params": [{"to": token_address, "data": data}, "latest"], "id": 1
    }
    try:
        response = requests.post(rpc_url, json=payload, timeout=5).json()
        if 'result' in response:
            return int(response['result'], 16)
    except:
        pass
    return 0

rpcs = [
    "https://polygon-rpc.com",
    "https://polygon.llamarpc.com",
    "https://1rpc.io/matic"
]
user = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"

tokens = {
    "Bridged USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "Native USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
}

for rpc in rpcs:
    print(f"Testing RPC: {rpc}")
    for name, addr in tokens.items():
        bal = get_token_balance(rpc, addr, user)
        print(f"  {name}: {bal / 1e6}")
