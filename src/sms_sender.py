# src/sms_sender.py
import json
import logging
import requests
from typing import Dict, Tuple


class SMSSender:
    def __init__(self, api_hostname: str, params_json: str):
        self.api_hostname = api_hostname
        self.params_mapping = json.loads(params_json)  # Converts stored JSON to dictionary
        self.logger = logging.getLogger(__name__)


    def send_sms(self, phone_number: str, message: str) -> Tuple[Dict, str]:
        """
        Sends an SMS using the API with dynamic parameter mapping.

        Args:
            phone_number: Recipient's phone number.
            message: Message content.

        Returns:
            Tuple containing:
                - API response JSON
                - Message status string
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

            # Try to parse response as JSON
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                # If response is not JSON, use text content
                response_json = {'text': response.text}

            # Extract status or determine based on response
            # This will need to be adjusted based on your API's response format
            if 'status' in response_json:
                message_status = response_json['status']
            elif 'success' in response_json:
                message_status = 'DELIVERED' if response_json['success'] else 'FAILED'
            else:
                message_status = 'SENT'  # Default status

            return response_json, message_status

        except requests.exceptions.RequestException as err:
            self.logger.error(f"SMS API request failed: {err}")
            message_status = f"REQUEST_FAILED: {type(err).__name__}"
            raise Exception(f"SMS API request failed: {err}")