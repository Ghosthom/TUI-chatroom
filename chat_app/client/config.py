"""Client configuration and setup."""

import sys
from typing import Optional, Tuple
from ..common.constants import DEFAULT_PORT, DEFAULT_NICKNAME, DEFAULT_HOST


def get_client_config() -> Optional[Tuple[str, str, int]]:
    """Interactive client configuration."""
    title = "CLIENT CONFIGURATION"
    line_length = 50
    title_padding = (line_length - len(title)) // 2

    print("\n" + "=" * line_length)
    print(" " * title_padding + title)
    print("=" * line_length)

    # Ask for nickname
    nickname = input("\nYour nickname: ").strip()
    if not nickname:
        nickname = DEFAULT_NICKNAME

    print("\nServer options:")
    print("  1. Localhost (127.0.0.1) - Server on this PC")
    print("  2. Hamachi               - Server on Hamachi network")
    print("  3. Custom                - Enter IP manually")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        server_host = "127.0.0.1"
    elif choice == "2":
        server_host = input("Server's Hamachi IP (e.g., 25.168.123.45): ").strip()
        if not server_host:
            server_host = DEFAULT_HOST
    elif choice == "3":
        server_host = input("Server IP address: ").strip()
        if not server_host:
            server_host = DEFAULT_HOST
    else:
        server_host = DEFAULT_HOST

    # Ask for port
    port_input = input(f"\nServer port [{DEFAULT_PORT}]: ").strip()
    if port_input:
        try:
            server_port = int(port_input)
        except ValueError:
            print(f"Invalid port, using {DEFAULT_PORT}")
            server_port = DEFAULT_PORT
    else:
        server_port = DEFAULT_PORT

    print(f"\n✓ Configuration:")
    print(f"  Nickname: {nickname}")
    print(f"  Server: {server_host}:{server_port}")

    confirm = input("\nConnect with this configuration? (y/n): ").strip().lower()

    if confirm in ['y', 'yes']:
        return nickname, server_host, server_port
    else:
        print("Operation cancelled")
        return None
