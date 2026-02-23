import logging
import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from agents import agent

_LOGGER = logging.getLogger("uvicorn.error")

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("GPT_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("CLAUDE_API_KEY")

app = FastAPI()


@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = uuid.uuid4().hex
    session_agent = _init_session_agent(session_id)
    _LOGGER.info("Session started: %s", session_id)
    try:
        while True:
            data = await websocket.receive_json()
            async for chunk in session_agent.answer_prompt(data["content"]):
                await websocket.send_json({"type": "chunk", "data": chunk})

    except WebSocketDisconnect as e:
        _LOGGER.info("Session ended: %s", session_id)


def _init_session_agent(session_id: str) -> agent.Agent:
    return agent.Agent(
        agent.AgentConfig(
            provider=agent.ModelProvider.ANTHROPIC,
            model=agent._DEFAULT_CLAUDE_MODEL,
            system_prompt=agent._AGENT_CONTEXT,
            tools=agent.init_session_tools(session_id=session_id),
        )
    )
