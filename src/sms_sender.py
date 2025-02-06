# src/sms_sender.py
import requests
import logging
from typing import Dict


class SMSSender:
    def __init__(self, api_hostname: str):
        self.api_hostname = api_hostname
        self.logger = logging.getLogger(__name__)

    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Send SMS via API and return response."""
        endpoint = f"{self.api_hostname}/api/send-sms"

        payload = {
            "phone_number": phone_number,
            "message": message
        }

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            self.logger.error(f"SMS API request failed: {err}")
            raise