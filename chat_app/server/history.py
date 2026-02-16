"""Chat history management."""

import os
from datetime import datetime
from typing import List, Dict, Optional


class ChatHistory:
    """Manages chat history and saving to files."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.entries: List[Dict] = []
        self.history_dir = "chat_history"

    def add(self, message: str, message_type: str = "message"):
        """Add a message to history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.entries.append({
            "timestamp": timestamp,
            "message": message,
            "type": message_type
        })

    def save(self) -> Optional[str]:
        """Save chat history to a file. Returns filename if successful."""
        if not self.entries:
            print("[+] No chat history to save")
            return None

        # Create history directory if needed
        if not os.path.exists(self.history_dir):
            try:
                os.makedirs(self.history_dir)
                print(f"[+] Created directory: {self.history_dir}")
            except Exception as e:
                print(f"[-] Error creating directory: {e}")
                self.history_dir = "."  # Fallback to current directory

        # Generate filename
        shutdown_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"chat-history_{shutdown_time}.txt"
        filepath = os.path.join(self.history_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 60 + "\n")
                f.write(f"CHAT HISTORY - Server {self.host}:{self.port}\n")
                f.write(f"Session started: {self.entries[0]['timestamp'] if self.entries else 'N/A'}\n")
                f.write(f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total messages: {len(self.entries)}\n")
                f.write("=" * 60 + "\n\n")

                # Write all messages
                for entry in self.entries:
                    prefix = f"[{entry['type'].upper()}]" if entry['type'] != "message" else ""
                    f.write(f"{prefix} [{entry['timestamp']}] {entry['message']}\n")

                # Write footer
                f.write("\n" + "=" * 60 + "\n")
                f.write("END OF CHAT HISTORY\n")
                f.write("=" * 60 + "\n")

            print(f"[+] Chat history saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"[-] Error saving chat history: {e}")
            return None
