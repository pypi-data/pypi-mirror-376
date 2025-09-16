# checkhim

Professional Python SDK for phone number verification via [checkhim.tech](https://checkhim.tech).

## Installation

```bash
pip install checkhim
```

## Usage

```python
import os
from checkhim.client import CheckHimClient

# Set your API key in the environment variable CHECKHIM_KEY
# or pass it directly to the client
client = CheckHimClient()

result = client.verify_number("+5511984339000")
print(result)  # {"carrier": "OI", "valid": true}
```

## Environment Variables
- `CHECKHIM_KEY`: Your API key for checkhim.tech


## Contributing

We welcome contributions from the community! To contribute:

1. Fork this repository and create your branch from `main`.
2. Install development dependencies and set up a virtual environment.
3. Make your changes with clear, well-documented code and tests.
4. Ensure all tests pass and code is linted.
5. Open a pull request with a clear description of your changes.

For questions or suggestions, open an issue or contact us at opensource@checkhim.tech.

## License
MIT
