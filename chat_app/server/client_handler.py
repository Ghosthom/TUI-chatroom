"""Client connection handler."""

import socket
import threading
import time
from typing import Dict, Any, Optional

from ..common.constants import BUFFER_SIZE, SOCKET_TIMEOUT
from ..common.protocols import format_user_message, format_system_message
from .moderation import ModerationManager


class ClientHandler:
    """Handles individual client connections."""

    def __init__(self, client: socket.socket, address: tuple,
                 server_ref, moderation: ModerationManager):
        self.client = client
        self.address = address
        self.server = server_ref
        self.moderation = moderation
        self.nickname: Optional[str] = None
        self.color: Optional[str] = None
        self.running = False

    def start(self):
        """Start handling this client."""
        self.running = True
        thread = threading.Thread(target=self._handle, daemon=True)
        thread.start()

    def _is_username_taken(self, nickname: str) -> bool:
        """Check if a username is already in use."""
        for client, info in self.server.client_info.items():
            if info["nickname"].lower() == nickname.lower():  # Case-insensitive comparison
                return True
        return False

    def _handle(self):
        """Main client handling loop."""
        try:
            print(f"[+] New connection: {self.address}")

            # Request nickname
            self.client.send("NICK".encode('utf-8'))
            self.nickname = self.client.recv(BUFFER_SIZE).decode('utf-8')

            # Check if username is already taken
            if self._is_username_taken(self.nickname):
                error_msg = "USERNAME_TAKEN|Username not available. There's already someone with that username in the chat. Choose a different one to join."
                self.client.send(error_msg.encode('utf-8'))
                self.client.close()
                print(f"[-] Client rejected - username '{self.nickname}' already taken: {self.address}")
                return

            self.color = self.moderation.assign_color()

            # Send confirmation
            self.client.send("CONNECTED".encode('utf-8'))

            # Register with server
            self.server.register_client(self.client, {
                "nickname": self.nickname,
                "color": self.color,
                "address": self.address
            })

            print(f"[+] Nickname received: {self.nickname} (color: {self.color})")

            # Notify join
            self.server.broadcast(
                f"{self.nickname} joined the chat!",
                exclude_client=None,  # Todos reciben el join
                is_system=True
            )

            # Message loop
            while self.running and self.server.running:
                try:
                    # Verificar si el cliente todavía está en la lista del servidor
                    if self.client not in self.server.clients:
                        print(f"[-] {self.nickname} removed from server list, disconnecting")
                        break

                    # Intentar recibir con timeout corto
                    self.client.settimeout(0.5)
                    data = self.client.recv(BUFFER_SIZE)

                    if not data:
                        print(f"[-] {self.nickname} disconnected")
                        break

                    message = data.decode('utf-8')
                    print(f"{self.nickname}: {message}")

                    # Check for private message
                    if message.startswith('/w '):
                        self._handle_private_message(message)
                        continue

                    # Check if muted
                    muted, remaining = self.moderation.is_muted(self.nickname)
                    if muted:
                        self.client.send(
                            format_system_message(
                                f"You are currently muted ({remaining}s remaining)"
                            ).encode('utf-8')
                        )
                        continue

                    # Normal message
                    self.server.add_to_history(f"{self.nickname}: {message}")
                    self.server.broadcast(
                        f"{self.nickname}: {message}",
                        self.client,
                        user_color=self.color
                    )

                except socket.timeout:
                    # Timeout es normal, solo verificar si seguimos conectados
                    continue
                except (ConnectionResetError, ConnectionAbortedError):
                    print(f"[-] Connection lost with {self.nickname}")
                    break
                except Exception as e:
                    print(f"[-] Error receiving from {self.nickname}: {e}")
                    break

        except Exception as e:
            print(f"[-] Error with {self.address}: {e}")
        finally:
            # Cleanup
            if self.nickname and self.client in self.server.clients:
                self.cleanup()
            else:
                try:
                    self.client.close()
                except:
                    pass

    def _handle_message(self, message: str):
        """Handle a message from client."""
        # Check for private message
        if message.startswith('/w '):
            self._handle_private_message(message)
            return

        # Check if muted
        muted, remaining = self.moderation.is_muted(self.nickname)
        if muted:
            self.client.send(
                format_system_message(
                    f"You are currently muted ({remaining}s remaining)"
                ).encode('utf-8')
            )
            return

        # Normal message
        print(f"{self.nickname}: {message}")
        self.server.add_to_history(f"{self.nickname}: {message}")

        self.server.broadcast(
            f"{self.nickname}: {message}",
            exclude_client=self.client,  # No enviar al remitente (él ya vio su mensaje localmente)
            user_color=self.color
        )

    def _handle_private_message(self, message: str):
        """Handle private message command."""
        parts = message.split(' ', 2)
        if len(parts) < 3:
            self.client.send(
                format_system_message("Usage: /w username message").encode('utf-8')
            )
            return

        receiver = parts[1]
        private_msg = parts[2]

        # Check self whisper
        if receiver == self.nickname:
            self.client.send(
                format_system_message("You cannot whisper to yourself").encode('utf-8')
            )
            return

        # Check if sender is muted
        muted, remaining = self.moderation.is_muted(self.nickname)
        if muted:
            self.client.send(
                format_system_message(
                    f"You are currently muted ({remaining}s remaining)"
                ).encode('utf-8')
            )
            return

        self.server.send_private_message(self.client, self.nickname,
                                         receiver, private_msg, self.color)

    def cleanup(self):
        """Clean up client resources."""
        self.running = False

        # Solo hacer broadcast si el cliente estaba registrado
        was_registered = self.client in self.server.clients

        # Unregister from server
        self.server.unregister_client(self.client, self.nickname, self.color)

        try:
            self.client.close()
        except:
            pass
