import requests
import json

API_URL = "https://poly-backend-nuf6.onrender.com/api/status"

try:
    response = requests.get(API_URL)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    data = response.json()
    print(json.dumps(data, indent=2))
except requests.exceptions.RequestException as e:
    print(f"ERROR: An error occurred while fetching status from {API_URL}: {e}")
