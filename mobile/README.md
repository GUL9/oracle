# Oracle Mobile

Minimal cross-platform (iOS + Android) native client for your existing WebSocket chat server.

## What it connects to

Your server exposes a WebSocket endpoint:

- `ws://<host>:8000/chat`
- Send: `{ "content": "..." }`
- Receive stream: `{ "type": "chunk", "data": "..." }`

This app connects to that endpoint and appends streamed `chunk` messages into the response view.
Responses are rendered as Markdown (including tappable links).

## Prereqs

- Node.js + npm
- Expo Go app on your phone (iOS/Android), or iOS Simulator / Android Emulator
- Backend running (from repo root):
  - `cd server && bash src/chat_server_launch.sh`
  - or `cd server/src && uvicorn chat_server:app --host 0.0.0.0 --port 8000 --reload`

## Configure the server URL

By default:

- iOS uses `ws://localhost:8000/chat` (works for iOS Simulator)
- Android emulator uses `ws://10.0.2.2:8000/chat`

For a physical iPhone (Expo Go), `localhost` is the phone, so you must point at your Mac’s LAN IP, e.g.:

```bash
EXPO_PUBLIC_WS_URL=ws://192.168.1.50:8000/chat npm start
```

Make sure the server is listening on `0.0.0.0` (not just `127.0.0.1`) and macOS firewall allows incoming connections.

## Run

From repo root:

```bash
cd mobile
npm start
```

Then:

- iOS: press `i` (simulator) or scan QR in Expo Go
- Android: press `a` (emulator) or scan QR in Expo Go
