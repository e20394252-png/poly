import os
from datetime import datetime, timezone, timedelta
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GAMMA_API_URL = "https://gamma-api.polymarket.com"

def get_proxy():
    proxies_str = os.getenv("PROXIES_LIST")
    if not proxies_str: return os.getenv("PROXY_URL")
    p_list = [p.strip() for p in proxies_str.split(',') if p.strip()]
    for p in p_list:
        try:
            r = requests.get("https://clob.polymarket.com/time", proxies={'http': p, 'https': p}, timeout=5)
            if r.status_code == 200: return p
        except: pass
    return None

PROXY = get_proxy()
proxies = {"http": PROXY, "https": PROXY} if PROXY else None

def get_active_events():
    url = f"{GAMMA_API_URL}/events?active=true&closed=false&order=endDate&ascending=true&limit=100"
    print(f"Fetching active events using proxy: {PROXY}")
    response = requests.get(url, proxies=proxies, timeout=60)
    if response.status_code == 200:
        return response.json()
    return []

def analyze():
    events = get_active_events()
    now = datetime.now(timezone.utc)
    min_time = now + timedelta(minutes=1)
    max_time = now + timedelta(days=7) 
    
    opportunities_85 = 0
    opportunities_scalp = 0
    total_markets = 0
    
    for event in events:
        end_date_str = event.get('endDate')
        if not end_date_str: continue
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        if not (min_time <= end_date <= max_time):
            continue
            
        for market in event.get('markets', []):
            if not market.get('active') or market.get('closed'):
                continue
            
            try:
                outcomes = json.loads(market.get('outcomes', '[]'))
                outcome_prices = json.loads(market.get('outcomePrices', '[]'))
                
                if len(outcomes) != len(outcome_prices): continue
                
                total_markets += 1
                for price_str in outcome_prices:
                    try:
                        price_f = float(price_str)
                        if 0.01 <= price_f <= 0.99:
                            opportunities_scalp += 1
                        if 0.85 <= price_f <= 0.99:
                            opportunities_85 += 1
                    except Exception:
                        pass
            except Exception:
                pass

    print(f"Total active short-term markets (next 7 days): {total_markets}")
    print(f"Found {opportunities_scalp} total scalp opportunities (1% - 99%)")
    print(f"Found {opportunities_85} high-probability opportunities (85% - 99%)")

if __name__ == "__main__":
    analyze()
