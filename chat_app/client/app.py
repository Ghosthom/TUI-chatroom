"""Main client application."""

import socket
import threading
import time
from typing import Optional, Dict

from textual import on
from textual.app import App
from textual.containers import Container
from textual.widgets import Input, RichLog

from rich.text import Text

from .ui.styles import CLIENT_CSS
from .ui.widgets import HeaderText
from ..common.constants import (
    PROTOCOL_NICK, PROTOCOL_SERVER_FULL,
    SELF_COLOR, COLOR_TIMESTAMP, COLOR_SYSTEM,
    COLOR_HELP, COLOR_ERROR, COLOR_PRIVATE,
    COLOR_DEFAULT, SOCKET_TIMEOUT, CONNECT_TIMEOUT,
    BUFFER_SIZE
)
from ..common.protocols import parse_server_message
from ..common.utils import get_timestamp


class ChatClient(App):
    """Group Chat client with TUI interface."""

    CSS = CLIENT_CSS
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("f1", "show_help", "Help"),
        ("up", "scroll_up", "Scroll Up"),
        ("down", "scroll_down", "Scroll Down"),
        ("pageup", "page_up", "Page Up"),
        ("pagedown", "page_down", "Page Down"),
        ("home", "scroll_home", "Go to Top"),
        ("end", "scroll_end", "Go to Bottom"),
    ]

    def __init__(self, nickname: str = "User",
                 server_host: str = '127.0.0.1',
                 server_port: int = 55555,
                 preconnected_socket: socket.socket = None):
        super().__init__()
        self.nickname = nickname
        self.server_host = server_host
        self.server_port = server_port
        self.client = preconnected_socket is not None
        self.client: Optional[socket.socket] = None
        self.connected = False
        self.user_colors: Dict[str, str] = {}

    def compose(self):
        yield HeaderText(self.nickname, self.server_host, self.server_port)
        yield Container(
            RichLog(id="messages", wrap=True, max_lines=1000),
            Container(
                Input(placeholder="Type your message and press Enter... (Type /help for more information)",
                      id="message_input"),
                id="input_container"
            ),
            id="chat_container"
        )
        # Note: Footer is intentionally omitted to match original design

    def on_mount(self):
        """When the application mounts."""
        self.title = f"Group Chat - {self.nickname}"
        self.query_one("#message_input").focus()

        if self.connected:
            self.add_message("Connection established successfully", "info")
            # Start receiving messages
            threading.Thread(target=self.receive_messages, daemon=True).start()
        else:
            self.add_message(f"Connecting to {self.server_host}:{self.server_port}...", "info")
            # Start connection in separate thread
            threading.Thread(target=self.connect_to_server, daemon=True).start()

    def get_user_display_name(self, username: str) -> str:
        """Get the display name for a user."""
        if username == self.nickname:
            return "You"  # Your own messages
        return username   # Other users

    def get_user_color(self, username: str, message_color: str = None) -> str:
        """Get color for a user, using cache or message color."""
        if username == self.nickname:
            return SELF_COLOR

        if message_color:
            self.user_colors[username] = message_color
            return message_color

        return self.user_colors.get(username, COLOR_DEFAULT)

    def format_user_message(self, timestamp: str, username: str,
                           message: str, user_color: str = None) -> Text:
        """Format a user message with colors and bold username."""
        timestamp_text = Text(f"[{timestamp}] ", style=COLOR_TIMESTAMP)

        display_name = self.get_user_display_name(username)
        color = self.get_user_color(username, user_color)

        username_text = Text(f"{display_name}: ", style=color)
        username_text.stylize("bold")

        message_text = Text(message, style="#ffffff")

        return timestamp_text + username_text + message_text

    def format_system_message(self, timestamp: str, message: str) -> Text:
        """Format a system message."""
        timestamp_text = Text(f"[{timestamp}] ", style=COLOR_TIMESTAMP)
        message_text = Text(message, style=COLOR_SYSTEM)
        return timestamp_text + message_text

    def format_info_message(self, timestamp: str, message: str) -> Text:
        """Format an info message."""
        return Text(f"[{timestamp}] {message}", style=COLOR_TIMESTAMP)

    def format_error_message(self, timestamp: str, message: str) -> Text:
        """Format an error message."""
        timestamp_text = Text(f"[{timestamp}] ", style=COLOR_TIMESTAMP)
        message_text = Text(message, style=COLOR_ERROR)
        return timestamp_text + message_text

    def format_help_message(self, timestamp: str, message: str) -> Text:
        """Format a help message."""
        timestamp_text = Text(f"[{timestamp}] ", style=COLOR_TIMESTAMP)
        message_text = Text(message, style=COLOR_HELP)
        return timestamp_text + message_text

    def format_private_message(self, timestamp: str, message: str) -> Text:
        """Format a private message."""
        if "]: " in message:
            formatted_text = Text(f"[{timestamp}] {message}", style=COLOR_PRIVATE)
            return formatted_text
        return Text(f"[{timestamp}] {message}", style=COLOR_PRIVATE)

    def add_message(self, message: str, message_type: str = "normal",
                   user_color: str = None):
        """Add message to RichLog with formatting."""
        timestamp = get_timestamp()

        # Determine format based on message type
        if message_type == "error":
            formatted_text = self.format_error_message(timestamp, message)
        elif message_type == "info":
            formatted_text = self.format_info_message(timestamp, message)
        elif message_type == "help":
            formatted_text = self.format_help_message(timestamp, message)
        elif message_type == "sent":
            formatted_text = self.format_user_message(timestamp, self.nickname,
                                                      message, SELF_COLOR)
        elif message_type == "received":
            parsed = parse_server_message(message)

            if parsed["is_system"]:
                # Handle system messages with special "You" treatment for join/leave
                content = parsed["content"]

                # Check if this is a join/leave message for the current user
                if content.endswith("joined the chat!"):
                    username = content.replace(" joined the chat!", "")
                    display_name = self.get_user_display_name(username)
                    formatted_text = self.format_system_message(
                        timestamp, f"[SYSTEM] {display_name} joined the chat!"
                    )
                elif content.endswith(" left the chat"):
                    username = content.replace(" left the chat", "")
                    display_name = self.get_user_display_name(username)
                    formatted_text = self.format_system_message(
                        timestamp, f"[SYSTEM] {display_name} left the chat"
                    )
                else:
                    formatted_text = self.format_system_message(timestamp, f"[SYSTEM] {content}")

            elif parsed["is_private"]:
                formatted_text = self.format_private_message(timestamp, parsed["content"])

            elif parsed["username"]:
                # Regular user message
                username = parsed["username"]
                actual_message = parsed["content"].split(": ", 1)[1] if ": " in parsed["content"] else parsed["content"]
                formatted_text = self.format_user_message(timestamp, username,
                                                          actual_message,
                                                          parsed["user_color"])
            else:
                formatted_text = Text(f"[{timestamp}] {message}", style="#ffffff")

        elif message_type == "system":
            formatted_text = self.format_system_message(timestamp, message)
        else:
            formatted_text = Text(f"[{timestamp}] {message}", style="#ffffff")

        # Update from main thread or secondary thread
        messages_widget = self.query_one("#messages")

        if threading.current_thread() == threading.main_thread():
            messages_widget.write(formatted_text)
        else:
            self.call_from_thread(messages_widget.write, formatted_text)

        print(f"CLIENT: [{timestamp}] {message}")

    def show_client_help(self):
        """Show help message to client."""
        help_text = """
╔══════════════════════════════════════════╗
║            GROUP CHAT HELP               ║
╠══════════════════════════════════════════╣
║ Commands:                                ║
║   /help         - Show this message      ║
║   /w user msg   - Whisper (private)      ║
║                                          ║
║ Navigation Shortcuts:                    ║
║   Ctrl+Q    - Quit application           ║
║   F1        - Show this help             ║
║   Up        - Scroll up                  ║
║   Down      - Scroll down                ║
║   Page Up   - Scroll page up             ║
║   Page Down - Scroll page down           ║
║   Home      - Go to top of chat          ║
║   End       - Go to bottom of chat       ║
║   Tab       - Focus next widget          ║
║   Shift+Tab - Focus previous widget      ║
║                                          ║
║ Chat Features:                           ║
║   • Your messages appear in blue         ║
║   • Others have unique colors            ║
║   • System messages are in yellow        ║
║   • Help messages are in cyan            ║
║   • Error messages are in red            ║
║   • Whispers in gray: [You ⭢ User]: msg  ║
║   • Only sender/receiver see whispers    ║
║   • Type normally for group chat         ║
╚══════════════════════════════════════════╝
"""
        lines = help_text.strip().split('\n')
        for line in lines:
            self.add_message(line, "help")

    def handle_client_command(self, message: str) -> bool:
        """Handle client-side commands."""
        message = message.strip()

        if message.startswith('/'):
            parts = message.split(maxsplit=1)
            command = parts[0].lower()

            if command == "/help":
                self.show_client_help()
                return True

        return False

    def connect_to_server(self):
        """Connect to the server."""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(CONNECT_TIMEOUT)
            self.client.connect((self.server_host, self.server_port))
            self.client.settimeout(None)
            self.connected = True

            # NICK protocol
            message = self.client.recv(BUFFER_SIZE).decode('utf-8')

            if message == PROTOCOL_NICK:
                self.client.send(self.nickname.encode('utf-8'))

                # Wait for response
                response = self.client.recv(BUFFER_SIZE).decode('utf-8')

                if response.startswith("USERNAME_TAKEN"):
                    # Username already taken - show error but don't exit automatically
                    error_msg = response.split('|', 1)[1] if '|' in response else "Username already taken"
                    self.add_message(f"ERROR: {error_msg}", "error")
                    self.add_message("Press Ctrl+Q to exit", "info")
                    self.connected = False

                elif response == "CONNECTED":
                    self.add_message("Connection established successfully", "info")
                    self.receive_messages()
                else:
                    self.add_message(f"Error: Unexpected response from server", "error")
                    self.connected = False

            elif message == PROTOCOL_SERVER_FULL:
                self.add_message("ERROR: Server is full. Try again later.", "error")
                self.add_message("Press Ctrl+Q to exit", "info")
                self.connected = False
            else:
                self.add_message(f"Error: Unexpected protocol", "error")
                self.add_message("Press Ctrl+Q to exit", "info")
                self.connected = False

        except socket.timeout:
            self.add_message(f"ERROR: Connection timeout to {self.server_host}:{self.server_port}", "error")
            self.add_message("Press Ctrl+Q to exit", "info")
            self.connected = False
        except ConnectionRefusedError:
            self.add_message(f"ERROR: Connection refused - server may be down", "error")
            self.add_message("Press Ctrl+Q to exit", "info")
            self.connected = False
        except Exception as e:
            self.add_message(f"Connection error: {e}", "error")
            self.add_message("Press Ctrl+Q to exit", "info")
            self.connected = False

    def receive_messages(self):
        """Receive messages from the server."""
        while self.connected:
            try:
                data = self.client.recv(BUFFER_SIZE)

                if not data:
                    self.add_message("Server disconnected", "error")
                    break

                message = data.decode('utf-8')

                if "shutting down" in message.lower():
                    self.add_message("Server is shutting down...", "system")
                    self.connected = False
                    break

                self.add_message(message, "received")

            except ConnectionAbortedError:
                self.add_message("Connection aborted", "error")
                self.connected = False
                break
            except ConnectionResetError:
                self.add_message("Connection reset by server", "error")
                self.connected = False
                break
            except Exception as e:
                self.add_message(f"Error receiving: {e}", "error")
                self.connected = False
                break

        self.connected = False
        if self.client:
            try:
                self.client.close()
            except:
                pass

    @on(Input.Submitted, "#message_input")
    def send_message(self):
        """Send message to server."""
        input_widget = self.query_one("#message_input")
        message = input_widget.value.strip()

        if not message:
            return

        if not self.connected:
            self.add_message("Cannot send message: Not connected to server", "error")
            self.add_message("Press Ctrl+Q to exit", "info")
            input_widget.value = ""
            return

        # Handle client commands first
        if message.startswith('/'):
            if self.handle_client_command(message):
                input_widget.value = ""
                return

        # Send message to server
        try:
            self.client.send(message.encode('utf-8'))

            # Show our message locally if it's not a whisper command
            if not message.startswith('/w '):
                self.add_message(message, "sent")
            input_widget.value = ""

        except Exception as e:
            self.add_message(f"Error sending: {e}", "error")
            self.connected = False

    # Navigation actions
    def action_scroll_up(self):
        self.query_one("#messages").scroll_up()

    def action_scroll_down(self):
        self.query_one("#messages").scroll_down()

    def action_page_up(self):
        self.query_one("#messages").scroll_page_up()

    def action_page_down(self):
        self.query_one("#messages").scroll_page_down()

    def action_scroll_home(self):
        self.query_one("#messages").scroll_home()

    def action_scroll_end(self):
        self.query_one("#messages").scroll_end()

    def action_show_help(self):
        self.show_client_help()

    def action_quit(self):
        """Exit the application."""
        self.connected = False
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.exit()
