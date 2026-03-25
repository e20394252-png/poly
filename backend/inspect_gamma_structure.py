import requests
import json
from datetime import datetime, timezone

def inspect_event_structure():
    # Fetch 10 truly active/soonest events
    url = "https://gamma-api.polymarket.com/events?active=true&closed=false&order=endDate&ascending=true&limit=10"
    try:
        response = requests.get(url)
        events = response.json()
        if not events:
            print("No events found.")
            return

        print(f"Inspecting first event: {events[0].get('title')}")
        print(json.dumps(events[0], indent=2))
        
        # Check available tags/categories in the response
        all_tags = set()
        for e in events:
             tags = e.get('tags')
             if tags:
                 for t in tags:
                     all_tags.add(t.get('label') if isinstance(t, dict) else str(t))
        
        print(f"\nSample Tags Found: {list(all_tags)[:20]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_event_structure()
