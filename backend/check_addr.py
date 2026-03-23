from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv()
pk = os.getenv("PRIVATE_KEY")
if pk:
    try:
        acc = Account.from_key(pk)
        print(f"Address: {acc.address}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No PK found")
