"""Custom widgets for the chat client."""

from textual.widgets import Static
from rich.text import Text
from typing import Optional


class HeaderText(Static):
    """Custom header widget with dynamic text."""

    def __init__(self, nickname: str, host: str, port: int):
        text = f"GROUP CHAT | Server: {host}:{port} | User: {nickname}"
        super().__init__(text, id="header")
