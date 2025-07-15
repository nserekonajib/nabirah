import os
import json
import uuid
import requests
import urllib3
from flask import current_app, session, redirect, url_for, flash, request, render_template
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PesaPal:
    def __init__(self):
        self.auth_url = "https://pay.pesapal.com/v3/api/Auth/RequestToken"
        self.api_url = "https://pay.pesapal.com/v3/api/"
        self.token = None

        self.consumer_key = os.getenv("PESAPAL_CONSUMER_KEY")
        self.consumer_secret = os.getenv("PESAPAL_CONSUMER_SECRET")

        # Register IPN only after authentication (defer this)
        self.ipn_id = None

    def authenticate(self):
        payload = json.dumps({
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        })
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

        try:
            response = requests.post(self.auth_url, headers=headers, data=payload, verify=False)
            response.raise_for_status()
            self.token = response.json()['token']
            # Register IPN after getting token
            self.ipn_id = self.register_ipn_url()
            return self.token
        except Exception as e:
            print("❌ Authentication failed:", e)
            return None

    def register_ipn_url(self):
        ipn_url = os.getenv("PESAPAL_IPN_URL", "https://yourdomain.com/ipn")
        endpoint = "URLSetup/RegisterIPN"
        payload = json.dumps({"url": ipn_url, "ipn_notification_type": "GET"})
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {self.token}"}
        try:
            response = requests.post(self.api_url + endpoint, headers=headers, data=payload, verify=False)
            response.raise_for_status()
            data = response.json()
            return data['ipn_id']
        except Exception as e:
            print("❌ IPN Registration failed:", e)
            return None
        

    def submit_order(self, amount, reference_id, callback_url, email, first_name, last_name):
        if not self.token:
            self.authenticate()

        endpoint = "Transactions/SubmitOrderRequest"
        payload = json.dumps({
            "id": reference_id,
            "currency": "UGX",
            "amount": str(amount),
            "description": "Customer Payment",
            "callback_url": callback_url,
            "notification_id": self.ipn_id,
            "billing_address": {
                "email_address": email,
                "phone_number": None,
                "country_code": "UG",
                "first_name": first_name,
                "middle_name": "",
                "last_name": last_name,
                "line_1": "",
                "line_2": "",
                "city": "Kampala",
                "state": "",
                "postal_code": "",
                "zip_code": ""
            }
        })
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {self.token}"}
        try:
            response = requests.post(self.api_url + endpoint, headers=headers, data=payload, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("❌ Order submission failed:", e)
            return None

    def verify_transaction_status(self, order_tracking_id):
        if not self.token:
            self.authenticate()

        endpoint = f"Transactions/GetTransactionStatus?orderTrackingId={order_tracking_id}"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {self.token}"}
        try:
            response = requests.get(self.api_url + endpoint, headers=headers, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("❌ Transaction verification failed:", e)
            return None

