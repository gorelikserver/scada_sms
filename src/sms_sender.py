# src/sms_sender.py
import requests
import logging
from typing import Dict
import json


import json
import logging
import requests
from typing import Dict, Any


import json
import logging
import requests
from typing import Dict


class SMSSender:
    def __init__(self, api_hostname: str, params_json: str):
        self.api_hostname = api_hostname
        self.params_mapping = json.loads(params_json)  # Converts stored JSON to dictionary
        self.logger = logging.getLogger(__name__)

    def send_sms(self, phone_number: str, message: str) -> Dict:
        """
        Sends an SMS using the API with dynamic parameter mapping.

        :param phone_number: Recipient's phone number.
        :param message: Message content.
        :return: API response JSON.
        """
        # Dynamically map fields
        params = {
            self.params_mapping["phone"]: phone_number,  # "mobileNumber"
            self.params_mapping["message"]: message,  # "message"
            self.params_mapping["app"]: self.params_mapping["app_value"]  # "application": "SCADA"
        }

        self.logger.info(f"POST request to: {self.api_hostname}")
        self.logger.info(f"Query params: {params}")

        try:
            response = requests.post(self.api_hostname, params=params)
            self.logger.info(f"Full URL: {response.url}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            self.logger.error(f"SMS API request failed: {err}")
            raise



