"""Utility functions for the chat application."""

import time
from datetime import datetime
from typing import Optional


def get_timestamp(format: str = "%H:%M:%S") -> str:
    """Get current timestamp."""
    return time.strftime(format)


def get_datetime_string() -> str:
    """Get full datetime string for filenames."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def validate_port(port: str) -> Optional[int]:
    """Validate and convert port number."""
    try:
        port_num = int(port)
        if 1024 <= port_num <= 65535:
            return port_num
        return None
    except ValueError:
        return None


def validate_nickname(nickname: str) -> bool:
    """Validate nickname (alphanumeric and basic punctuation)."""
    if not nickname or len(nickname) > 20:
        return False
    # Allow letters, numbers, underscores, hyphens
    return all(c.isalnum() or c in ('-', '_') for c in nickname)
