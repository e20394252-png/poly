import requests

proxy_addr = '0x0411F017251a5918422FECc2cDeA558a0A5c6115'
url = f'https://api.polygonscan.com/api?module=account&action=tokentx&address={proxy_addr}&startblock=0&endblock=99999999&page=1&offset=100&sort=desc'

try:
    r = requests.get(url, timeout=10)
    data = r.json()
    if data['status'] == '1':
        print(f"Found {len(data['result'])} token transfers. Tokens involved:")
        tokens = set()
        for tx in data['result']:
            tokens.add((tx['tokenName'], tx['tokenSymbol'], tx['contractAddress']))
        for t in tokens:
            print(t)
    else:
        print('Query failed:', data)
except Exception as e:
    print('FAILED:', e)
