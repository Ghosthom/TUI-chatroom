"""Server configuration."""

from typing import Optional, Tuple
from ..common.constants import DEFAULT_PORT, DEFAULT_MAX_CLIENTS, DEFAULT_HOST
from ..common.utils import validate_port


def get_server_config() -> Optional[Tuple[str, int, int]]:
    """Interactive server configuration."""
    title = "SERVER CONFIGURATION"
    line_length = 50
    title_padding = (line_length - len(title)) // 2

    print("\n" + "=" * line_length)
    print(" " * title_padding + title)
    print("=" * line_length)

    print("\nHost options:")
    print("  1. 127.0.0.1     - Local connections only")
    print("  2. Hamachi IP    - Your Hamachi IP (e.g., 25.x.x.x)")
    print("  3. Custom IP     - Enter IP manually")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        host = "127.0.0.1"
    elif choice == "2":
        host = input("Enter your Hamachi IP (e.g., 25.168.123.45): ").strip()
        if not host:
            host = DEFAULT_HOST
    elif choice == "3":
        host = input("Enter host IP address: ").strip()
        if not host:
            host = DEFAULT_HOST
    else:
        host = DEFAULT_HOST

    # Ask for port
    port_input = input(f"\nPort [{DEFAULT_PORT}]: ").strip()
    if port_input:
        validated = validate_port(port_input)
        if validated:
            port = validated
        else:
            print(f"Invalid port, using {DEFAULT_PORT}")
            port = DEFAULT_PORT
    else:
        port = DEFAULT_PORT

    # Ask for max clients
    max_input = input(f"\nMaximum clients [{DEFAULT_MAX_CLIENTS}]: ").strip()
    if max_input:
        try:
            max_clients = int(max_input)
            if max_clients < 1:
                max_clients = DEFAULT_MAX_CLIENTS
        except ValueError:
            print(f"Invalid number, using {DEFAULT_MAX_CLIENTS}")
            max_clients = DEFAULT_MAX_CLIENTS
    else:
        max_clients = DEFAULT_MAX_CLIENTS

    print(f"\n✓ Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Max clients: {max_clients}")

    confirm = input("\nStart server with this configuration? (y/n): ").strip().lower()

    if confirm in ['y', 'yes']:
        return host, port, max_clients
    else:
        print("Operation cancelled")
        return None
