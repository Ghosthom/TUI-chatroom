#!/usr/bin/env python3
"""Entry point for running the chat server."""

from chat_app.server.server import ChatServer
from chat_app.server.config import get_server_config


def main():
    """Main entry point."""
    config = get_server_config()

    if config:
        host, port, max_clients = config
        server = ChatServer(host=host, port=port, max_clients=max_clients)

        try:
            server.start()
        except KeyboardInterrupt:
            print("\n[+] Server interrupted by user")
        except Exception as e:
            print(f"[-] Server error: {e}")


if __name__ == "__main__":
    main()
