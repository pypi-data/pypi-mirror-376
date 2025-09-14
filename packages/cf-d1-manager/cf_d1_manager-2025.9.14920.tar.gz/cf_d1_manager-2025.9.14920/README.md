[![PyPI version](https://badge.fury.io/py/cf_d1_manager.svg)](https://badge.fury.io/py/cf_d1_manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/cf_d1_manager)](https://pepy.tech/project/cf_d1_manager)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# cf_d1_manager

A Python package to easily retrieve Cloudflare D1 configuration from environment variables.

## Installation

To install `cf_d1_manager`, use pip:

```bash
pip install cf_d1_manager
```

## Usage

The `cf_d1_manager` package provides a single function, `get_cf_d1_config()`, which reads required Cloudflare D1 configuration from environment variables.

### Environment Variables Required:

- `CF_API_TOKEN`: Your Cloudflare API token.
- `CF_ACCOUNT_ID`: Your Cloudflare account ID.
- `CF_D1_DATABASE_ID`: The ID of your D1 database.

### Example

Here's how you can use `get_cf_d1_config()` in your Python script:

```python
import os
from cf_d1_manager import get_cf_d1_config

# Set dummy environment variables for demonstration
os.environ["CF_API_TOKEN"] = "your_api_token"
os.environ["CF_ACCOUNT_ID"] = "your_account_id"
os.environ["CF_D1_DATABASE_ID"] = "your_database_id"

try:
    config = get_cf_d1_config()
    print("Cloudflare D1 Configuration:")
    print(f"  API Token: {config['CF_API_TOKEN']}")
    print(f"  Account ID: {config['CF_ACCOUNT_ID']}")
    print(f"  Database ID: {config['CF_D1_DATABASE_ID']}")
except ValueError as e:
    print(f"Error: {e}")

# Clean up dummy environment variables
del os.environ["CF_API_TOKEN"]
del os.environ["CF_ACCOUNT_ID"]
del os.environ["CF_D1_DATABASE_ID"]
```

If any of the required environment variables are not set, `get_cf_d1_config()` will raise a `ValueError`.

## Author

Eugene Evstafev <hi@eugene.plus>

## Repository

https://github.com/chigwell/cf_d1_manager

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/cf_d1_manager/issues).

## License

`cf_d1_manager` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).