# Oracle Codebase Guide for AI Agents

## Project Overview

**Oracle** is a full-stack multi-model fact-checking application with:

- **Backend**: Python FastAPI server with LangGraph-based agent orchestration
- **Frontend**: React Native/Expo cross-platform mobile app
- **Architecture**: Multi-LLM coordination (Claude, Gemini, GPT-4) for nuanced fact verification

## Key Architecture Patterns

### Backend (Python)

**Location**: `server/src/`

**Core Components**:

- `agent.py`: LangGraph ReAct agent that orchestrates multiple LLM tools (Gemini, Claude, GPT-4) to fact-check by comparing responses
- `main.py`: FastAPI server with message endpoint at `POST /receive_message`
- Uses LangChain framework for cross-model invocation

**Multi-LLM Pattern** (critical for this project):

```python
# From agent.py - each tool is a separate LLM provider
@tool
def ask_gemini(prompt: str) -> str:
    """Query Gemini model"""

@tool
def ask_claude(prompt: str) -> str:
    """Query Claude model"""

# Agent synthesizes responses into agreement/disagreement analysis
```

**Key Concepts**:

- Tools are LLM endpoints, not utility functions
- System prompts differ: `_AGENT_CONTEXT` for orchestration, `_TOOL_CONTEXT` for individual queries
- API key mapping: `CLAUDE_API` → `ANTHROPIC_API_KEY`, `GPT_API` → `OPENAI_API_KEY`, etc.

### Frontend (React Native/Expo)

**Location**: `client/`

**Tech Stack**: Expo with file-based routing

- Entry point: `app/_layout.tsx`
- Tabs structure: `app/(tabs)/` for main navigation
- Components use theming from `constants/Colors.ts` and hooks in `hooks/`

**Key Files**:

- `app/(tabs)/index.tsx`: Main explore screen
- `components/ThemedView.tsx` & `ThemedText.tsx`: Branded UI components
- Styling follows Expo conventions with theme context

## Development Workflows

### Backend Development

**Setup**:

```bash
cd server/src
source .venv/bin/activate  # or conda activate oracle
pip install -r requirements.txt
```

**Running the Server**:

```bash
# Via launch script
bash launch.sh
# Or direct uvicorn
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Dependencies**:

- FastAPI, Uvicorn (HTTP server)
- LangChain, LangGraph (multi-agent framework)
- LangSmith (optional observability)
- API SDKs: Anthropic, OpenAI, Google GenAI

### Frontend Development

**Setup**:

```bash
cd client
npm install
npm start  # or npx expo start
```

**Run on Device**:

- iOS: `npm run ios`
- Android: `npm run android`
- Web: `npm run web`

**Linting**: `npm run lint`

**Fresh Start**: `npm run reset-project` (moves starter code to `app-example/`)

## Project Conventions

### Code Style

**Python**:

- Dataclasses for models (see `Message` in `main.py`)
- Type hints consistently used
- LangChain tools use `@tool` decorator with docstrings

**TypeScript/React**:

- File-based routing in `app/` directory (Expo Router convention)
- Component names match files (PascalCase)
- Theme colors centralized in `constants/Colors.ts`

### Environment Variables

Backend expects:

- `CLAUDE_API`: Anthropic API key
- `GPT_API`: OpenAI API key
- `GEMINI_API`: Google GenAI API key

### Message Format

FastAPI endpoint expects:

```python
@dataclass
class Message:
    content: str
```

## Critical Integration Points

1. **Backend → Frontend Communication**: Frontend sends message to `/receive_message` endpoint
2. **Multi-LLM Orchestration**: Agent calls tools in parallel, synthesizes results
3. **Routing**: Frontend uses Expo file-based routing; layout files define navigation structure

## Common Patterns to Avoid

- **Don't**: Add simple utility functions as `@tool` decorators (reserved for LLM providers)
- **Don't**: Hardcode API keys; always use environment variables
- **Don't**: Modify Expo routing manually; use file/folder naming conventions

## Key Files Reference

- Architecture decisions: [agent.py](server/src/agent.py), [main.py](server/src/main.py)
- Frontend structure: [\_layout.tsx](client/app/_layout.tsx), [Colors.ts](client/constants/Colors.ts)
- Build scripts: [launch.sh](server/src/launch.sh), [package.json](client/package.json)
