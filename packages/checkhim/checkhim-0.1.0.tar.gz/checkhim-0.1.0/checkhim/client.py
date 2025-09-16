
import os
import requests
from .exceptions import InvalidAPIKeyError, VerificationError

class CheckHimClient:
    """
    Client for checkhim.tech phone number verification API.
    """
    API_URL = "https://api.checkhim.tech/api/v1/verify"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CHECKHIM_KEY")
        if not self.api_key:
            raise InvalidAPIKeyError("API key must be provided via argument or CHECKHIM_KEY environment variable.")

    def verify_number(self, number: str) -> dict:
        payload = {"number": number, "type": "frontend"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=10)
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                # Try to parse error details from API response
                try:
                    error_data = response.json()
                    error_message = error_data.get("error")
                    error_code = error_data.get("code")
                except Exception:
                    error_message = response.text
                    error_code = None
                if response.status_code == 401:
                    raise InvalidAPIKeyError("Invalid API key or unauthorized access.") from e
                raise VerificationError(error_message, error_code) from e
            data = response.json()
            # If API returns error fields, treat as error
            code = data.get("code")
            if data.get("error") or (code and (code.startswith("REJECTED") or code.startswith("UNDELIVERABLE") or code.startswith("TEMPORARY_FAILURE") or code.startswith("SERVICE_UNAVAILABLE"))):
                raise VerificationError(data.get("error"), code)
            return {
                "carrier": data.get("carrier"),
                "valid": data.get("valid")
            }
        except InvalidAPIKeyError:
            raise
        except requests.RequestException as e:
            raise VerificationError(f"Request failed: {e}") from e
        except Exception as e:
            # If it's already a VerificationError, propagate as is
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(f"Unexpected error: {e}") from e
