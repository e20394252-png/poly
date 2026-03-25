import requests
import json
from datetime import datetime, timezone, timedelta

def check_gamma_events():
    # Adding closed=false and sorting by endDate
    url = "https://gamma-api.polymarket.com/events?active=true&closed=false&order=endDate&ascending=true&limit=100"
    try:
        response = requests.get(url)
        events = response.json()
        print(f"Fetched {len(events)} events.")
        
        now = datetime.now(timezone.utc)
        min_time = now + timedelta(minutes=1)
        max_time = now + timedelta(hours=24)
        
        print(f"Current UTC: {now.isoformat()}")
        print(f"Filter Window: {min_time.isoformat()} to {max_time.isoformat()}")
        
        matching = 0
        for event in events:
            end_date_str = event.get('endDate')
            title = event.get('title')
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                diff = end_date - now
                if min_time <= end_date <= max_time:
                    matching += 1
                    print(f"[MATCH] {title} | End: {end_date_str} (in {diff})")
                else:
                    if matching < 10:
                         print(f"[SKIP] {title} | End: {end_date_str} (in {diff})")
            else:
                print(f"[NO END DATE] {title}")
                
        print(f"\nSummary: {matching}/{len(events)} match the 24h filter.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_gamma_events()
