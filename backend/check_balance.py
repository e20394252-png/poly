import requests
address = "0xD57d3F5BB3A3a2ce4796F9B7b8a9f01F51150485"
# Use a public RPC or a block explorer API
# USDC.e on Polygon: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
url = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress=0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359&address={address}&tag=latest"
# native usdc
res = requests.get(url).json()
print(f"Native USDC: {res.get('result')}")

url_e = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress=0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174&address={address}&tag=latest"
res_e = requests.get(url_e).json()
print(f"Bridged USDC: {res_e.get('result')}")
