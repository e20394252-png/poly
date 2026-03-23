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
    try:
        response = requests.post(rpc_url, json=payload).json()
        if 'result' in response:
            return int(response['result'], 16)
    except:
        pass
    return 0

rpc = "https://polygon-rpc.com"
user = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"

tokens = {
    "Bridged USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "Native USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "DAI": "0x8f3Cf7ad23Cd3Ca15b7468248871526266d691f8"
}

for name, addr in tokens.items():
    bal = get_token_balance(rpc, addr, user)
    print(f"{name}: {bal / 1e6}")
