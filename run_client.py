#!/usr/bin/env python3
"""Entry point for running the chat client."""

import sys
from chat_app.client.app import ChatClient
from chat_app.client.config import get_client_config


def main():
    """Main entry point."""
    # Get configuration
    if len(sys.argv) > 1:
        nickname = sys.argv[1]
        if len(sys.argv) > 2:
            server_host = sys.argv[2]
            server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 55555
        else:
            config = get_client_config()
            if not config:
                sys.exit(0)
            nickname, server_host, server_port = config
    else:
        config = get_client_config()
        if not config:
            sys.exit(0)
        nickname, server_host, server_port = config

    # Start the UI - dejar que la UI maneje la conexión
    app = ChatClient(
        nickname=nickname,
        server_host=server_host,
        server_port=server_port
    )
    app.run()


if __name__ == "__main__":
    main()
