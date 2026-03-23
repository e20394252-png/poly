import requests
from datetime import datetime, timezone, timedelta
import json

GAMMA_API_URL = "https://gamma-api.polymarket.com"
PROXY_URL = "http://wxbZy0:km81Gm@194.53.190.7:8000"

def fetch_active_events():
    print("Fetching active events...")
    all_events = []
    limit = 100
    offset = 0
    max_events = 500
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    while len(all_events) < max_events:
        url = f"{GAMMA_API_URL}/events?active=true&closed=false&limit={limit}&offset={offset}"
        try:
            response = requests.get(url, proxies=proxies, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_events.extend(data)
            offset += limit
        except Exception as e:
            print(f"Error: {e}")
            break
            
    return all_events

def check_opportunities():
    events = fetch_active_events()
    now = datetime.now(timezone.utc)
    min_time = now + timedelta(minutes=1)
    max_time = now + timedelta(hours=24)
    
    found_any = False
    print(f"\nScanning {len(events)} events for opportunities closing between {min_time} and {max_time}...")
    
    for event in events:
        end_date_str = event.get('endDate')
        if not end_date_str:
            continue
            
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except:
            continue
            
        if min_time <= end_date <= max_time:
            found_any = True
            print(f"\n[!] SHORT-TERM EVENT: {event.get('title')}")
            print(f"    Closes: {end_date}")
            
            markets = event.get('markets', [])
            for market in markets:
                if not market.get('active') or market.get('closed'):
                    continue
                
                print(f"    - Market: {market.get('question')}")
                outcomes = json.loads(market.get('outcomes', '[]'))
                prices = json.loads(market.get('outcomePrices', '[]'))
                
                for i in range(len(outcomes)):
                    outcome = outcomes[i]
                    price = float(prices[i]) if i < len(prices) else 0
                    
                    if 0.85 <= price < 1.00:
                        print(f"      >>> POTENTIAL TRADE: {outcome} @ ${price:.2f} (MATCHES BOT CRITERIA)")
                    else:
                        print(f"      - {outcome} @ ${price:.2f}")
    
    if not found_any:
        print("\nNo events found closing in the next 24 hours.")

if __name__ == "__main__":
    check_opportunities()
