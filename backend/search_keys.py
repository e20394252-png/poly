import re
import os

def search_pb(file_path):
    print(f"Searching {file_path}...")
    pattern = re.compile(b'0x[0-9a-fA-F]{64}')
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            matches = pattern.findall(content)
            for m in matches:
                print(f"Found: {m.decode()}")
    except Exception as e:
        print(f"Error: {e}")

search_pb(r"C:\Users\user\.gemini\antigravity\conversations\25161e68-af19-40f2-b26b-d33e42a8cb64.pb")
search_pb(r"C:\Users\user\.gemini\antigravity\conversations\1c086504-76a3-4453-bd5c-d00a720d3b38.pb")
search_pb(r"C:\Users\user\.gemini\antigravity\conversations\3424b7a1-ac96-4a7c-8b61-8385923ec141.pb")
