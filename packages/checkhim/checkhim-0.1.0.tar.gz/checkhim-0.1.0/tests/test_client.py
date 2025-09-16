import os
import pytest
from checkhim.client import CheckHimClient
from checkhim.exceptions import InvalidAPIKeyError, VerificationError

import requests
from unittest.mock import patch

class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code
        self.text = str(json_data)
    def json(self):
        return self._json
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)

@patch('requests.post')
def test_verify_number_success(mock_post):
    mock_post.return_value = MockResponse({"carrier": "UNITEL", "valid": True, "code": "DELIVERED_TO_HANDSET"}, 200)
    client = CheckHimClient(api_key="testkey")
    result = client.verify_number("+5511984339000")
    assert result == {"carrier": "UNITEL", "valid": True}

@patch('requests.post')
def test_verify_number_error(mock_post):
    mock_post.return_value = MockResponse({"error": "verification failed: Network is forbidden (code: 6)", "code": "REJECTED_NETWORK"}, 400)
    client = CheckHimClient(api_key="testkey")
    with pytest.raises(VerificationError) as exc:
        client.verify_number("244921000111")
    assert exc.value.code == "REJECTED_NETWORK"
    assert "Network is forbidden" in str(exc.value)

@patch('requests.post')
def test_invalid_api_key(mock_post):
    mock_post.return_value = MockResponse({}, 401)
    client = CheckHimClient(api_key="badkey")
    with pytest.raises(InvalidAPIKeyError):
        client.verify_number("+5511984339000")
