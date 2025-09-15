"""Configuration loading for gac.

Handles environment variable and .env file precedence for application settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from gac.constants import EnvDefaults, Logging


def load_config() -> dict[str, str | int | float | bool]:
    """Load configuration from $HOME/.gac.env, then ./.env, then environment variables."""
    user_config = Path.home() / ".gac.env"
    if user_config.exists():
        load_dotenv(user_config)
    project_env = Path(".env")
    if project_env.exists():
        load_dotenv(project_env, override=True)

    config = {
        "model": os.getenv("GAC_MODEL"),
        "temperature": float(os.getenv("GAC_TEMPERATURE", EnvDefaults.TEMPERATURE)),
        "max_output_tokens": int(os.getenv("GAC_MAX_OUTPUT_TOKENS", EnvDefaults.MAX_OUTPUT_TOKENS)),
        "max_retries": int(os.getenv("GAC_RETRIES", EnvDefaults.MAX_RETRIES)),
        "log_level": os.getenv("GAC_LOG_LEVEL", Logging.DEFAULT_LEVEL),
        "warning_limit_tokens": int(os.getenv("GAC_WARNING_LIMIT_TOKENS", EnvDefaults.WARNING_LIMIT_TOKENS)),
    }

    return config
