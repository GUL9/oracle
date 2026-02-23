from typing import TypeAlias

import asyncio
import json
import websockets

from rich.console import Console
from rich.markdown import Markdown


SERVER_URL = "ws://localhost:8000/chat"

_Websocket: TypeAlias = websockets.WebSocketClientProtocol
console = Console()


class ChatClient:

    def __init__(self, server_url: str):
        self.server_url = server_url

    async def connect(self) -> _Websocket:
        """Establish WebSocket connection to the server."""
        try:
            socket = await websockets.connect(self.server_url)
            print("✓ Connected!")
            return socket

        except ConnectionRefusedError:
            print(f"✗ Could not connect to: {self.server_url}")
            raise

        except websockets.exceptions.WebSocketException as e:
            print(f"✗ WebSocket error: {e}")
            raise

    async def chat(self, socket: _Websocket):
        listen_task = asyncio.create_task(_listen_for_messages(socket))
        event_loop = asyncio.get_event_loop()

        while True:
            # Run input in a thread to avoid blocking
            user_input = await event_loop.run_in_executor(None, input, "You: ")

            if user_input.lower() == "quit":
                print("Goodbye!")
                listen_task.cancel()
                _disconnect(socket)
                break

            await _send_message(user_input, socket)


async def _disconnect(socket: _Websocket) -> None:
    """Close the WebSocket connection."""
    await socket.close()


async def _send_message(content: str, socket: _Websocket) -> None:
    """Send a message to the server."""
    message = json.dumps({"content": content})
    await socket.send(message)


async def _listen_for_messages(socket: _Websocket) -> None:
    """Listen for incoming messages from the server and display as markdown."""

    print("\nOracle:\n")
    async for message in socket:
        data = json.loads(message)

        if data.get("type") == "chunk":
            response = data.get("data", "")
            try:
                console.print(Markdown(response))
            except Exception as e:
                print("✗ Markdown render error:", e)


async def main():
    """Main entry point for the client."""
    client = ChatClient(server_url=SERVER_URL)
    socket = await client.connect()
    await client.chat(socket)


if __name__ == "__main__":
    asyncio.run(main())
