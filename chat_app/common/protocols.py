"""Protocol definitions for client-server communication."""

from typing import Tuple, Optional
from .constants import SYSTEM_PREFIX, PRIVATE_PREFIX


def parse_server_message(message: str) -> dict:
    """
    Parse a message from the server.

    Returns a dict with type, content, and metadata.
    """
    result = {
        "raw": message,
        "type": "normal",
        "content": message,
        "user_color": None,
        "username": None,
        "is_system": False,
        "is_private": False
    }

    # Check for system message
    if message.startswith(SYSTEM_PREFIX):
        result["type"] = "system"
        result["is_system"] = True
        result["content"] = message[len(SYSTEM_PREFIX):].strip()
        return result

    # Check for private message
    if message.startswith(PRIVATE_PREFIX):
        result["type"] = "private"
        result["is_private"] = True
        content = message[len(PRIVATE_PREFIX):].strip()

        # Extract color if present
        if "|" in content:
            msg_content, color = content.rsplit("|", 1)
            result["content"] = msg_content.strip()
            result["user_color"] = color
        else:
            result["content"] = content
        return result

    # Check for colored user message
    if "|" in message:
        content, color = message.rsplit("|", 1)
        result["content"] = content
        result["user_color"] = color

        # Extract username if possible
        if ": " in content:
            username, _ = content.split(": ", 1)
            result["username"] = username

    return result


def format_user_message(username: str, message: str, color: str) -> str:
    """Format a user message for broadcast."""
    return f"{username}: {message}|{color}"


def format_system_message(message: str) -> str:
    """Format a system message."""
    return f"{SYSTEM_PREFIX} {message}"


def format_private_message(sender: str, receiver: str, message: str) -> Tuple[str, str]:
    """
    Format private messages for sender and receiver.
    Returns (sender_format, receiver_format)
    """
    sender_fmt = f"{PRIVATE_PREFIX} [You ⭢ {receiver}]: {message}|#666666"
    receiver_fmt = f"{PRIVATE_PREFIX} [{sender} ⭢ You]: {message}|#666666"
    return sender_fmt, receiver_fmt
