from dotenv import load_dotenv
import requests
import os
load_dotenv()
# Initialize Supabase client outside routes to reuse
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ROLE")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def get_client_by_id(client_id):
    url = f"{SUPABASE_URL}/rest/v1/clients?id=eq.{client_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json()[0] if res.ok and res.json() else None


def update_client_status(client_id, new_status):
    url = f"{SUPABASE_URL}/rest/v1/clients?id=eq.{client_id}"
    data = {"status": new_status}
    res = requests.patch(url, headers=HEADERS, json=data)
    return res.ok


def insert_client_financing(client_id, amount, investment_date, expected_payback):
    url = f"{SUPABASE_URL}/rest/v1/client_financing"
    data = {
        "client_id": client_id,
        "amount": amount,
        "investment_date": investment_date,
        "expected_payback": expected_payback
    }
    res = requests.post(url, headers=HEADERS, json=data)
    return res.ok
