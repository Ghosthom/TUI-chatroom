# TUI chatroom

A terminal-based group chat application with support for private messages, moderation commands, and a TUI interface built with Textual.

## 📝 Note About Development

This project was developed through **vibe-coding** - a mix of Spanish and English comments, AI-assisted development, and iterative refinement. The code works perfectly, but you might find sporadic bilingual comments throughout.

## Features

### 👥 Group Chat
- Real-time messaging between multiple users
- Each user gets a unique color for easy identification
- Your messages appear in blue, others in their assigned colors
- Join/leave notifications with smart "You" handling
- Timestamps in gray for all messages

### 🔒 Private Messages (Whispers)
- Send private messages using `/w username message`
- Only sender and receiver see the messages
- Private messages appear in gray with arrow notation: `[You ⭢ User]: message`
- Cannot whisper to yourself

### 🛡️ Moderation (Server Console)
- /kick username - Kick a user
- /mute username seconds - Mute a user
- /unmute username - Unmute a user
- /list - List connected users

Server can also broadcast messages by simply typing and pressing Enter.

### 🎨 TUI Interface
- Dark theme with syntax highlighting
- Scrollable chat history with keyboard navigation
- **System messages** in yellow
- **Error messages** in red
- **Help messages** in cyan
- **Private messages** in gray

### ⌨️ Keyboard Shortcuts
- Ctrl+Q - Quit
- F1 - Show help
- Up/Down - Scroll
- Page Up/Down - Page scroll
- Home/End - Jump to top/bottom

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:
```
git clone https://github.com/Ghosthom/TUI-chatroom.git
cd TUI-chatroom
```
2. Install dependencies:
```
pip install -r requirements.txt
```
## Usage

### Starting the Server

The server handles client connections and moderation commands.

    python run_server.py

You'll be guided through the configuration:

    ==================================================
                   SERVER CONFIGURATION
    ==================================================

    Host options:
      1. 127.0.0.1     - Local connections only
      2. Hamachi IP    - Your Hamachi IP (e.g., 25.x.x.x)
      3. Custom IP     - Enter IP manually

    Select option (1-3): 1

    Port [55555]: 

    Maximum clients [5]: 

    ✓ Configuration:
      Host: 127.0.0.1
      Port: 55555
      Max clients: 5

    Start server with this configuration? (y/n): y

Once running, you'll see the server console where you can:

- Type messages to broadcast to all clients
- Use moderation commands (prefixed with /)
- Type shutdown to gracefully stop the server
- Type quit to close console (server continues running)

### Starting a Client

The client provides the TUI interface for chatting.

    python run_client.py

Configuration guide:

    ==================================================
                   CLIENT CONFIGURATION
    ==================================================
    
    Your nickname: John
    
    Server options:
      1. Localhost (127.0.0.1) - Server on this PC
      2. Hamachi               - Server on Hamachi network
      3. Custom                - Enter IP manually

    Select option (1-3): 1

    Server port [55555]: 

    ✓ Configuration:
      Nickname: John
      Server: 127.0.0.1:55555

    Connect with this configuration? (y/n): y

## Error Handling

The application handles various error scenarios gracefully:

- Username already taken: Shows error message and lets you exit manually with Ctrl+Q
- Server full: Informs you and lets you try another server
- Connection refused: Alerts if server is down
- Timeout: Notifies if server doesn't respond
- Muted user: Prevents sending messages and shows remaining time
- Invalid command: Provides usage hints

## Chat History

The server can save chat history when shutting down:

    [+] Chat history contains 42 messages
    Do you want to save the conversation? (y/n): y
    [+] Chat history saved to: chat_history/chat-history_2024-01-15_14-30-22.txt

History files are stored in the chat_history/ directory with timestamps.

## Common Issues & Solutions

### "Username already taken" but you're the first one

This happens if you try to connect with the same username from another terminal while the first one is still connected. Each username must be unique in the chat.

### Client opens and closes immediately

Check that the server is running and the port is correct. The client shows error messages before closing.

### Can't connect from another computer

- Make sure the server is configured with the correct IP
- Check firewall settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Textual - TUI framework for Python
- Rich for beautiful text formatting
- Inspired by classic IRC clients

## Support

For issues or questions:

- Open an issue on GitHub
- Check existing issues for solutions
- Include error messages and steps to reproduce
