"""CSS styles for the Textual client UI."""

CLIENT_CSS = """
Screen {
    background: #080808;
    overflow: hidden;
    layout: vertical;
}

#header {
    height: 3;
    background: #080808;
    color: #666666;
    padding: 0 1;
    text-style: bold;
    border: heavy #333333;
}

#chat_container {
    layout: vertical;
    overflow: hidden;
}

#messages {
    height: 1fr;
    border: heavy #333333;
    margin: 0;
    padding: 1;
    background: #080808;
    color: #ffffff;
    overflow-y: auto;
    scrollbar-size: 1 1;
    scrollbar-color: #666666 #262626;
}

#input_container {
    height: auto;
    min-height: 3;
    border: heavy #333333;
    margin: 0;
    padding: 1;
    background: #080808;
    layout: horizontal;
    overflow: hidden;
}

#message_input {
    width: 100%;
    background: #080808;
    color: #ffffff;
    padding: 0 1;
    min-height: 3;
    border: none;
}

#message_input:focus {
    border: none;
    outline: none;
}

Input.-focus {
    border: none;
}
"""
