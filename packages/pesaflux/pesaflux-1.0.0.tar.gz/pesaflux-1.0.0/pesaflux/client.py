import requests
import json


class PesaFlux:
    BASE_URL = "https://api.pesaflux.co.ke/v1"

    def __init__(self, api_key: str, email: str):
        """
        Initialize the PesaFlux client.
        :param api_key: Your PesaFlux API key
        :param email: Email registered on PesaFlux
        """
        self.api_key = api_key
        self.email = email
        self.headers = {"Content-Type": "application/json"}

    def stk_push(self, amount: int, msisdn: str, reference: str) -> dict:
        """
        Initiate an STK Push.
        """
        payload = {
            "api_key": self.api_key,
            "email": self.email,
            "amount": str(amount),
            "msisdn": msisdn,
            "reference": reference,
        }
        url = f"{self.BASE_URL}/initiatestk"
        res = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(res)

    def transaction_status(self, transaction_request_id: str) -> dict:
        """
        Verify the status of a transaction.
        """
        payload = {
            "api_key": self.api_key,
            "email": self.email,
            "transaction_request_id": transaction_request_id,
        }
        url = f"{self.BASE_URL}/transactionstatus"
        res = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(res)

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return {"status": "error", "message": str(e)}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON response"}
