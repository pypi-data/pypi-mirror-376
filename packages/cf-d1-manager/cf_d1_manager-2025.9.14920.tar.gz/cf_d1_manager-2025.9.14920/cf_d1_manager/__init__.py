# __init__.py
import os
from typing import Any, Dict, Optional

def _must_env(key: str) -> str:
    """Get environment variable or raise if not set."""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Environment variable '{key}' must be set.")
    return value

def get_cf_d1_config() -> Dict[str, str]:
    """
    Retrieves Cloudflare D1 configuration from environment variables.

    This function reads the following environment variables:
    - CF_API_TOKEN: Your Cloudflare API token.
    - CF_ACCOUNT_ID: Your Cloudflare account ID.
    - CF_D1_DATABASE_ID: The ID of your D1 database.

    It raises a ValueError if any of these required environment variables are not set.

    Returns:
        A dictionary containing the CF_API_TOKEN, CF_ACCOUNT_ID, and CF_D1_DATABASE_ID.

    Raises:
        ValueError: If any of the required environment variables are not set.
    """
    cf_api_token = _must_env("CF_API_TOKEN")
    cf_account_id = _must_env("CF_ACCOUNT_ID")
    cf_d1_database_id = _must_env("CF_D1_DATABASE_ID")

    return {
        "CF_API_TOKEN": cf_api_token,
        "CF_ACCOUNT_ID": cf_account_id,
        "CF_D1_DATABASE_ID": cf_d1_database_id,
    }