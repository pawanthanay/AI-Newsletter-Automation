"""
Configuration loader — reads and validates config.yaml
"""

import os
import yaml
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
HISTORY_DIR = PROJECT_ROOT / "history"
LOGS_DIR = PROJECT_ROOT / "logs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def load_config(path: str = None) -> dict:
    """Load and validate configuration from YAML file."""
    config_path = Path(path) if path else CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    _validate_config(config)
    _ensure_directories()

    logger.info(f"Configuration loaded from {config_path}")
    return config


def _validate_config(config: dict):
    """Validate required configuration fields."""
    required_fields = {
        "accounts": "List of X accounts is required",
        "email": "Email configuration is required",
        "schedule": "Schedule configuration is required",
        "keywords": "AI keywords list is required",
    }

    for field, message in required_fields.items():
        if field not in config or not config[field]:
            raise ValueError(f"Config error: {message}")

    email = config.get("email", {})
    if not email.get("sender") or email["sender"] == "your_email@gmail.com":
        logger.warning("⚠️  Email sender not configured — update config.yaml")

    if not email.get("app_password") or email["app_password"] == "your_gmail_app_password":
        logger.warning("⚠️  Gmail app password not configured — update config.yaml")


def _ensure_directories():
    """Create required directories if they don't exist."""
    for directory in [HISTORY_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def get_accounts(config: dict) -> list:
    """Get list of X account usernames."""
    return [acc.lstrip("@").strip() for acc in config.get("accounts", [])]


def get_keywords(config: dict) -> list:
    """Get AI filtering keywords (lowercased)."""
    return [kw.lower() for kw in config.get("keywords", [])]


def get_exclude_keywords(config: dict) -> list:
    """Get exclusion keywords (lowercased)."""
    return [kw.lower() for kw in config.get("exclude_keywords", [])]
