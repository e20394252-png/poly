import requests
import json

def get_token_balance(rpc_url, token_address, user_address):
    # balanceOf(address) selector: 0x70a08231
    data = "0x70a08231" + user_address[2:].zfill(64)
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": token_address, "data": data}, "latest"],
        "id": 1
    }
    response = requests.post(rpc_url, json=payload).json()
    if 'result' in response:
        return int(response['result'], 16)
    return 0

rpc = "https://polygon-rpc.com"
user = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"

# Bridged USDC.e
usdc_e = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
bal_e = get_token_balance(rpc, usdc_e, user)
print(f"Bridged USDC.e: {bal_e / 1e6} USDC")

# Native USDC
usdc_n = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
bal_n = get_token_balance(rpc, usdc_n, user)
print(f"Native USDC: {bal_n / 1e6} USDC")
