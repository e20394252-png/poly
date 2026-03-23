import requests
import json

def fetch_one_event():
    url = "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            with open("debug_event.json", "w", encoding="utf-8") as f:
                json.dump(data[0], f, indent=2)
            print("Done. Saved to debug_event.json")
        else:
            print("No events found.")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")
        print(f"Response Body: {response.text}")

if __name__ == "__main__":
    fetch_one_event()
