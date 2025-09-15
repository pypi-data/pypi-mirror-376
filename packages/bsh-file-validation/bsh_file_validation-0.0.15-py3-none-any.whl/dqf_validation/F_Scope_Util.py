"""
This module provides a utility function to interact with DBUtils services
and return the required secret values.

Author          : Keerthana Subramanian
Creation date   : Feb 13, 2024
Updated by      : Keerthana Subramanian
Updation date   : Mar 27, 2024
"""

from databricks.sdk.runtime import dbutils


def get_values_from_secrets_scope(scope_name, key_list) -> list:
    """Retrieve values from a specified AWS Secrets Manager secret.
    Args:
        - scope name (str): Databricks scope name.
        - key_list (list[str]): List of keys to extract values from the secret.
    Returns:
        - dict: Dictionary containing key-value pairs from the specified keys in the secret.
    """
    try:
        secret_list = [
            dbutils.secrets.get(scope=scope_name, key=key)  # noqa: F821
            for key in key_list
        ]
        return secret_list
    except KeyError as ex:
        raise KeyError("Invalid key name passed in key_list") from ex
