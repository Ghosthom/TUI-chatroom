"""Shared constants for the chat application."""

# Protocol messages
PROTOCOL_NICK = "NICK"
PROTOCOL_SERVER_FULL = "SERVER_FULL"
PROTOCOL_USERNAME_TAKEN = "USERNAME_TAKEN"
PROTOCOL_CONNECTED = "CONNECTED"

# Message types
MSG_TYPE_SYSTEM = "system"
MSG_TYPE_PRIVATE = "private"
MSG_TYPE_SERVER = "server"
MSG_TYPE_NORMAL = "normal"
MSG_TYPE_ERROR = "error"
MSG_TYPE_INFO = "info"
MSG_TYPE_HELP = "help"

# System message prefixes
SYSTEM_PREFIX = "[SYSTEM]"
PRIVATE_PREFIX = "[PRIVATE]"

# Colors
USER_COLORS = [
    "#4a9c4a",  # Green
    "#d46b08",  # Orange
    "#a34a4a",  # Red
    "#9c4a9c",  # Magenta
    "#4a9c9c",  # Cyan
]

# Self message color
SELF_COLOR = "#4a76a3"  # Blue

# UI Colors
COLOR_TIMESTAMP = "#666666"  # Gray
COLOR_SYSTEM = "#b5a642"     # Yellow
COLOR_HELP = "#4a9c9c"       # Cyan
COLOR_ERROR = "#a34a4a"      # Red
COLOR_PRIVATE = "#666666"    # Gray
COLOR_DEFAULT = "#666666"    # Gray fallback

# Default values
DEFAULT_PORT = 55555
DEFAULT_MAX_CLIENTS = 5
DEFAULT_NICKNAME = "User"
DEFAULT_HOST = "127.0.0.1"

# Network settings
SOCKET_TIMEOUT = 1.0
CONNECT_TIMEOUT = 10.0
BUFFER_SIZE = 1024
