import requests
import time

proxies_list = [
    'http://modeler_10K1pe:KuwPa8FuLMy0@167.179.91.8:11416',
    'http://modeler_sWMIcy:eMXYgWdIabNH@167.179.91.8:11417',
    'http://modeler_dNMMg4:rcuxHR6q8tiM@167.179.91.8:11418'
]

urls = [
    'https://relayer-v2.polymarket.com',
    'https://data-api.polymarket.com/positions?user=0x0411F017251a5918422FECc2cDeA558a0A5c6115'
]

for p in proxies_list:
    name = p.split('@')[1]
    print(f'Testing proxy: {name}')
    proxies = {'http': p, 'https': p}
    for url in urls:
        target = url.split('/')[2]
        t0 = time.time()
        try:
            r = requests.get(url, proxies=proxies, timeout=10)
            print(f'  {target}: OK! {time.time()-t0:.2f}s (Status: {r.status_code})')
        except Exception as e:
            print(f'  {target}: FAILED! {type(e).__name__} (Time: {time.time()-t0:.2f}s)')
    print('-'*40)
