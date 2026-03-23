import requests

EOA = "0xD57d3F5BB3A3a2ce4796F9B7b8a9f01F51150485"
PROXY = "0x0411F017251a5918422FECc2cDeA558a0A5c6115"
tokens = [("USDC.e", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"), ("Native USDC", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")]

def check_bal(addr, name):
    print(f"\nChecking {name} ({addr}):")
    for t_name, t_addr in tokens:
        data = "0x70a08231" + addr[2:].zfill(64)
        payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": t_addr, "data": data}, "latest"], "id": 1}
        try:
            res = requests.post("https://1rpc.io/matic", json=payload, timeout=10).json()
            bal = int(res['result'], 16) / 1e6
            print(f"  {t_name}: ${bal:.6f}")
        except Exception as e:
            print(f"  {t_name}: FAILED ({e})")

check_bal(EOA, "Owner (EOA)")
check_bal(PROXY, "Proxy Wallet")
