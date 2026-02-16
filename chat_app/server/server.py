"""Main server implementation."""

import socket
import threading
import time
from typing import Dict, List, Optional, Any

from ..common.constants import (
    PROTOCOL_SERVER_FULL, DEFAULT_PORT, DEFAULT_MAX_CLIENTS,
    SOCKET_TIMEOUT, BUFFER_SIZE
)
from ..common.protocols import (
    format_system_message, format_private_message, format_user_message
)
from .history import ChatHistory
from .moderation import ModerationManager
from .client_handler import ClientHandler


class ChatServer:
    """Main chat server."""

    def __init__(self, host: str = '127.0.0.1', port: int = DEFAULT_PORT,
                 max_clients: int = DEFAULT_MAX_CLIENTS):
        self.host = host
        self.port = port
        self.max_clients = max_clients

        # Server state
        self.running = False
        self.is_shutting_down = False
        self.server_socket: Optional[socket.socket] = None

        # Client management
        self.clients: List[socket.socket] = []
        self.client_info: Dict[socket.socket, Dict] = {}

        # Managers
        self.moderation = ModerationManager()
        self.history = ChatHistory(host, port)

        # Threads
        self.accept_thread: Optional[threading.Thread] = None
        self.console_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.server_socket.settimeout(SOCKET_TIMEOUT)

            self.running = True
            print(f"[+] Server listening on {self.host}:{self.port}")
            print(f"[+] Maximum capacity: {self.max_clients} clients")

            self.history.add(f"Server started on {self.host}:{self.port}", "server")

            # Start console thread
            self.console_thread = threading.Thread(target=self._console_loop, daemon=True)
            self.console_thread.start()

            # Accept connections
            self._accept_loop()

        except KeyboardInterrupt:
            print("\n[+] Server interrupted by user")
        except Exception as e:
            print(f"[-] Server error: {e}")
        finally:
            self.cleanup()

    def _accept_loop(self):
        """Main accept loop for new connections."""
        while self.running:
            try:
                client, address = self.server_socket.accept()

                # Check capacity before creating handler
                if len(self.clients) < self.max_clients:
                    # NO agregamos a self.clients aquí - eso lo hará register_client
                    handler = ClientHandler(client, address, self, self.moderation)
                    handler.start()
                else:
                    client.send(PROTOCOL_SERVER_FULL.encode('utf-8'))
                    client.close()
                    print(f"[-] Connection rejected - server full: {address}")

            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    print(f"[-] Socket error: {e}")
                break

    def _console_loop(self):
        """Server console input loop."""
        print(f"\n[SERVER CONSOLE] Maximum {self.max_clients} clients.")
        print("[+] Type messages to broadcast to all clients")
        print("[+] Type /help for moderation commands")
        print("[+] Type 'shutdown' to stop the server gracefully")
        print("[+] Type 'quit' to close console (server continues)")

        while self.running:
            try:
                user_input = input("\n[SERVER] > ").strip()

                if user_input.lower() == 'quit':
                    print("Closing server console...")
                    break
                elif user_input.lower() == 'shutdown':
                    print("Shutting down server gracefully...")
                    self.running = False
                    break
                elif user_input.startswith('/'):
                    result = self._handle_moderation_command(user_input)
                    print(f"[MOD] {result}")
                    self.history.add(f"Server command: {user_input} -> {result}", "server")
                elif user_input:
                    print(f"[SERVER] Sending: {user_input}")
                    self.broadcast(user_input, None, is_system=True)
                    self.history.add(f"Server broadcast: {user_input}", "server")

            except (KeyboardInterrupt, EOFError):
                print("\nShutting down server gracefully...")
                self.running = False
                break
            except Exception as e:
                print(f"Console error: {e}")

    def _handle_moderation_command(self, command: str) -> str:
        """Handle moderation commands."""
        parts = command.split()
        if not parts:
            return "Invalid command"

        cmd = parts[0].lower()

        if cmd == "/kick" and len(parts) >= 2:
            return self._kick_user(parts[1])

        elif cmd == "/mute" and len(parts) >= 3:
            try:
                seconds = int(parts[2])
                if seconds <= 0:
                    return "Mute time must be positive"
                return self._mute_user(parts[1], seconds)
            except ValueError:
                return "Invalid mute time. Use: /mute username seconds"

        elif cmd == "/unmute" and len(parts) >= 2:
            return self._unmute_user(parts[1])

        elif cmd == "/list":
            users = self.moderation.get_user_list(self.client_info)
            if users:
                return "Connected users: " + ", ".join(users)
            return "No users connected"

        elif cmd == "/help":
            return self._get_help_text()

        return f"Unknown command: {cmd}. Type /help for available commands."

    def _get_help_text(self) -> str:
        """Get moderation help text."""
        return """
Moderation Commands:
  /kick username      - Kick a user from the server
  /mute username secs - Mute a user for specified seconds
  /unmute username    - Unmute a user
  /list               - List all connected users
  /help               - Show this help message
Server Commands:
  shutdown            - Gracefully shutdown the server
  quit                - Close server console (server continues running)
        """.strip()

    def _kick_user(self, nickname: str) -> str:
        """Kick a user from the server."""
        client_to_kick = None
        client_info = None

        for client, info in self.client_info.items():
            if info["nickname"] == nickname:
                client_to_kick = client
                client_info = info
                break

        if client_to_kick and client_info:
            try:
                # 1. PRIMERO: Remover de todas las listas para que no reciba más broadcasts
                if client_to_kick in self.clients:
                    self.clients.remove(client_to_kick)
                if client_to_kick in self.client_info:
                    del self.client_info[client_to_kick]

                # 2. Notificar a los demas ANTES de cerrar la conexión
                broadcast_msg = f"{nickname} has been kicked from the server"
                self.broadcast(broadcast_msg, None, is_system=True)
                self.history.add(broadcast_msg, "system")

                # 3. Liberar recursos de moderación
                self.moderation.release_color(client_info["color"])
                self.moderation.unmute(nickname)

                # 4. Enviar mensaje de kick al usuario
                try:
                    kick_msg = format_system_message("You have been kicked from the server")
                    client_to_kick.send(kick_msg.encode('utf-8'))
                except:
                    pass  # Si ya falló, no importa

                # 5. Cerrar el socket inmediatamente
                try:
                    client_to_kick.shutdown(socket.SHUT_RDWR)  # Forzar cierre de ambas direcciones
                except:
                    pass
                client_to_kick.close()

                print(f"[-] {nickname} kicked from server")
                return f"User {nickname} kicked successfully"

            except Exception as e:
                print(f"[-] Error kicking user {nickname}: {e}")
                return f"Error kicking user {nickname}: {e}"

        return f"User {nickname} not found"

    def _mute_user(self, nickname: str, seconds: int) -> str:
        """Mute a user."""
        # Delegar al ModerationManager
        mute_until = self.moderation.mute(nickname, seconds)

        # Encontrar al usuario muteado
        muted_client = None
        for client, info in self.client_info.items():
            if info["nickname"] == nickname:
                muted_client = client
                break

        # Mensaje personalizado para el usuario muteado
        if muted_client:
            try:
                personal_msg = format_system_message(f"You have been muted for {seconds} seconds")
                muted_client.send(personal_msg.encode('utf-8'))
            except:
                pass

        # Mensaje para todos los demás (no incluye al muteado)
        message = f"{nickname} has been muted for {seconds} seconds"
        self.broadcast(message, muted_client, is_system=True)  # Pasamos muted_client como sender para excluirlo
        self.history.add(message, "system")

        return f"User {nickname} muted for {seconds} seconds"

    def _unmute_user(self, nickname: str) -> str:
        """Unmute a user."""
        if self.moderation.unmute(nickname):
            # Encontrar al usuario desmuteado
            unmuted_client = None
            for client, info in self.client_info.items():
                if info["nickname"] == nickname:
                    unmuted_client = client
                    break

            # Mensaje personalizado para el usuario desmuteado
            if unmuted_client:
                try:
                    personal_msg = format_system_message("You have been unmuted")
                    unmuted_client.send(personal_msg.encode('utf-8'))
                except:
                    pass

            # Mensaje para todos los demás
            message = f"{nickname} has been unmuted"
            self.broadcast(message, unmuted_client, is_system=True)  # Excluir al usuario desmuteado
            self.history.add(message, "system")

            return f"User {nickname} unmuted"

        return f"User {nickname} is not muted"

    def register_client(self, client: socket.socket, info: Dict):
        """Register a new client."""
        # Verificación adicional para evitar duplicados
        for existing_client, existing_info in self.client_info.items():
            if existing_info["nickname"].lower() == info["nickname"].lower():
                print(f"[-] Race condition: {info['nickname']} already registered")
                return

        # Add to clients list - SOLO AQUÍ se agrega
        if client not in self.clients:
            self.clients.append(client)
            print(f"[+] Client added to clients list. Total: {len(self.clients)}")

        self.client_info[client] = info
        print(f"[+] Client info registered for {info['nickname']}")

    def unregister_client(self, client: socket.socket, nickname: str, color: str):
        """Unregister a client."""
        print(f"[-] Unregistering {nickname}")

        was_in_clients = client in self.clients
        was_in_info = client in self.client_info

        if was_in_clients:
            self.clients.remove(client)
            print(f"[-] Removed from clients list. Remaining: {len(self.clients)}")

        if was_in_info:
            del self.client_info[client]
            print(f"[-] Removed from client_info")

        self.moderation.release_color(color)
        self.moderation.unmute(nickname)

        if was_in_clients and was_in_info and self.running:
            message = f"{nickname} left the chat"
            self.broadcast(message, None, is_system=True)
            self.history.add(message, "system")
            print(f"[-] Broadcast: {nickname} left the chat")
        else:
            print(f"[-] No broadcast for {nickname} (was_in_clients={was_in_clients}, was_in_info={was_in_info}, running={self.running})")

        print(f"[-] {nickname} disconnected (color released: {color})")

    def add_to_history(self, message: str, message_type: str = "message"):
        """Add message to history."""
        self.history.add(message, message_type)

    def broadcast(self, message: str, exclude_client: Optional[socket.socket] = None,
                 user_color: str = None, is_system: bool = False):
        """
        Send message to all connected clients except exclude_client.
        """
        if not self.running:
            return

        if is_system:
            formatted = format_system_message(message)
        elif user_color:
            formatted = f"{message}|{user_color}"
        else:
            formatted = message

        disconnected = []
        # Iterar sobre una copia de la lista
        for client in self.clients[:]:
            # Saltar el cliente a excluir
            if exclude_client and client == exclude_client:
                continue

            try:
                # Verificar si el socket sigue válido
                if client.fileno() == -1:  # Socket cerrado
                    disconnected.append(client)
                    continue

                client.send(formatted.encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError, OSError):
                disconnected.append(client)
            except Exception:
                disconnected.append(client)

        # Clean up disconnected clients
        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)
                if client in self.client_info:
                    info = self.client_info[client]
                    self.moderation.release_color(info["color"])
                    del self.client_info[client]
                    print(f"[-] {info['nickname']} removed during broadcast")

    def send_private_message(self, sender_client: socket.socket,
                            sender: str, receiver: str,
                            message: str, sender_color: str):
        """Send private message between users."""
        receiver_client = None
        for client, info in self.client_info.items():
            if info["nickname"] == receiver:
                receiver_client = client
                break

        if not receiver_client:
            sender_client.send(
                format_system_message(f"User '{receiver}' is not connected").encode('utf-8')
            )
            return

        # Format and send messages
        sender_fmt, receiver_fmt = format_private_message(sender, receiver, message)

        try:
            sender_client.send(sender_fmt.encode('utf-8'))
        except:
            pass

        try:
            receiver_client.send(receiver_fmt.encode('utf-8'))
        except:
            pass

        # Add to history
        self.history.add(f"{sender} ⭢ {receiver}: {message}", "private")
        print(f"[PRIVATE] {sender} ⭢ {receiver}: {message}")

    def cleanup(self):
        """Clean up server resources."""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        print("[+] Shutting down server...")

        # Notify all clients
        for client in self.clients[:]:
            try:
                client.send(format_system_message("Server is shutting down...").encode('utf-8'))
            except:
                pass

        # Close all connections
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass

        # Wait a moment
        time.sleep(1)

        # Save history if requested
        if self.history.entries:
            print(f"\n[+] Chat history contains {len(self.history.entries)} messages")
            while True:
                try:
                    save = input("Do you want to save the conversation? (y/n): ").strip().lower()
                    if save in ['y', 'yes']:
                        self.history.save()
                        break
                    elif save in ['n', 'no']:
                        print("[+] Chat history will not be saved")
                        break
                except (KeyboardInterrupt, EOFError):
                    print("\n[+] Saving cancelled")
                    break

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                print("[+] Server socket closed")
            except Exception as e:
                print(f"[-] Error closing server socket: {e}")

        print("[+] Server stopped successfully")
