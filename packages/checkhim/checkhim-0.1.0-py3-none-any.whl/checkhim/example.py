import os
from checkhim.client import CheckHimClient

# Set your API key in the environment variable CHECKHIM_KEY
# or pass it directly to the client
client = CheckHimClient()

try:
    result = client.verify_number("+5511984339000")
    print(result)  # {"carrier": "UNITEL", "valid": true}
except Exception as e:
    print(f"Verification failed: {e}")
