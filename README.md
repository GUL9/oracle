# Oracle

Multi-model fact-checking application using Claude, Gemini, and GPT-4 for consensus-based verification.

## Stack

- **Server**: Python FastAPI + LangGraph agent orchestration
- **Mobile**: React Native/Expo
- **Client**: Python WebSocket testing client

## Prerequisites

Python 3.9+, Node.js 18+, API keys from [Google AI](https://makersuite.google.com/app/apikey), [OpenAI](https://platform.openai.com/api-keys), and [Anthropic](https://console.anthropic.com/settings/keys)

## Setup

```bash
# Server
cd server && bash requirements_install.sh
cd src && cp .env.example .env  # Add your API keys

# Mobile
cd mobile && npm install

# Client (optional)
cd client && bash requirements_install.sh
```

## Running

```bash
# Server (WebSocket on http://127.0.0.1:8000/chat)
cd server/src && bash chat_server_launch.sh

# Mobile (press i/a for iOS/Android)
cd mobile && npm start

# Test client
cd client/src && bash client_launch.sh
```

## How It Works

1. WebSocket query → Agent orchestrates parallel LLM calls
2. Claude, Gemini, and GPT-4 provide independent analysis
3. Agent synthesizes consensus/disagreement
4. Real-time streaming response

Key files: [chat_server.py](server/src/chat_server.py), [agent.py](server/src/agents/agent.py)

## Security

⚠️ Never commit `.env` files. Rotate API keys immediately if exposed.
