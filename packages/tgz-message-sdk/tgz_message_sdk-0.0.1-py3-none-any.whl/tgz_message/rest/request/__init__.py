import requests

from ..domain import BaseDomain

class APIRequest(BaseDomain):
    """
    Reusable request sender that builds the URL dynamically.
    """

    def send_api_request(
            self,
            messaging_product:str,
            delivery_type: str,
            account_sid: str,
            auth_token: str,
            payload: dict
    ):

        url = f"{self.BASE_URL}{messaging_product}/{delivery_type}/"

        response = requests.post(
            url,
            headers={
                'X-Account-SID': account_sid,
                'X-Auth-Token': auth_token,
            },
            json=payload
        )

        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else {}
        }