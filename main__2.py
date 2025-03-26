import json
import asyncio
import websockets

DJANGO_WS_URL = "ws://127.0.0.1:8000/connect-ai/"  # Replace with your actual WebSocket URL

async def websocket_client():
    """ Connects to Django Channels WebSocket, sends a message, and listens for responses """
    try:
        async with websockets.connect(DJANGO_WS_URL) as websocket:
            print("✅ Connected to Django WebSocket")

            # Example: Send a message to Django WebSocket
            message = {"command": "generate_image", "message": "Hello from Python client!"}
            await websocket.send(json.dumps(message))
            print(f"📤 Sent: {message}")

            # Keep listening for incoming messages
            while True:
                response = await websocket.recv()
                print(f"📩 Received: {response}")

                data = response
                breakpoint()

                await websocket.close()
                break

    except websockets.ConnectionClosed:
        print("⚠️ Connection closed. Reconnecting in 5 seconds...")
        await asyncio.sleep(5)
        await websocket_client()  # Auto-reconnect

# Run the WebSocket client
print("Initiating Run")
asyncio.run(websocket_client())
print("Ran")
