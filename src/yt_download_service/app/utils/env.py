import os


def get_or_raise_env(variable_name: str) -> str:
    """Get an environment variable or raises an error if it's not found."""
    value = os.getenv(variable_name)
    if value is None:
        raise ValueError(f"Environment variable {variable_name} not set")
    return value
