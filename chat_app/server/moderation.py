"""Moderation commands and user management."""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Set
import socket
from ..common.constants import USER_COLORS
from ..common.protocols import format_system_message


class ModerationManager:
    """Handles all user moderation (mute, kick, ban, etc.)"""

    def __init__(self):
        self.muted_users: Dict[str, datetime] = {}
        self.available_colors = USER_COLORS.copy()
        self.user_colors: Dict[str, str] = {}
        self.kicked_users: Set[str] = set()  # Historial de kicks recientes

    # Color management
    def assign_color(self) -> str:
        """Assign a unique color to a new user."""
        if self.available_colors:
            return self.available_colors.pop(0)
        return "#666666"

    def release_color(self, color: str):
        """Release a color when a user disconnects."""
        if color in USER_COLORS and color not in self.available_colors:
            self.available_colors.append(color)

    # Mute management
    def is_muted(self, nickname: str) -> Tuple[bool, Optional[int]]:
        """Check if a user is muted. Returns (is_muted, seconds_remaining)."""
        if nickname in self.muted_users:
            if self.muted_users[nickname] > datetime.now():
                remaining = self.muted_users[nickname] - datetime.now()
                return True, int(remaining.total_seconds())
            else:
                del self.muted_users[nickname]
        return False, None

    def mute(self, nickname: str, seconds: int) -> datetime:
        """Mute a user for specified seconds. Returns mute expiry."""
        mute_until = datetime.now() + timedelta(seconds=seconds)
        self.muted_users[nickname] = mute_until
        return mute_until

    def unmute(self, nickname: str) -> bool:
        """Unmute a user. Returns True if user was muted."""
        if nickname in self.muted_users:
            del self.muted_users[nickname]
            return True
        return False

    # Kick management
    def kick(self, client: socket.socket, nickname: str, color: str,
             server_ref) -> Tuple[bool, str]:
        """
        Kick a user from the server.
        Returns (success, message)
        """
        try:
            # Enviar mensaje de kick
            kick_msg = format_system_message("You have been kicked from the server")
            client.send(kick_msg.encode('utf-8'))

            # Close socket
            client.close()

            # Register kick
            self.kicked_users.add(nickname)

            # Free resources
            self.release_color(color)
            self.unmute(nickname)

            return True, f"User {nickname} kicked successfully"

        except Exception as e:
            return False, f"Error kicking user {nickname}: {e}"

    def was_kicked(self, nickname: str) -> bool:
        """Check if a user was recently kicked."""
        return nickname in self.kicked_users

    def clear_kick_history(self, nickname: str):
        """Clear kick history for a user (when they reconnect later)."""
        if nickname in self.kicked_users:
            self.kicked_users.remove(nickname)

    # User listing
    def get_user_list(self, users_info: Dict) -> List[str]:
        """Get formatted list of users with status."""
        users = []
        for client, info in users_info.items():
            muted, remaining = self.is_muted(info["nickname"])
            status = f"muted ({remaining}s)" if muted else "active"
            users.append(f"{info['nickname']} ({status})")
        return users
