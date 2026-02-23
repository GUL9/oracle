import logging
import dataclasses
import enum
import threading
from typing import Any, AsyncGenerator, Callable, Sequence

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
_DEFAULT_CLAUDE_MODEL = "claude-3-7-sonnet-latest"
_DEFAULT_GPT_MODEL = "o4-mini"


_AGENT_CONTEXT = """
You are a fact checker that provides nuanced answers by asking different sources.
You have received tools to ask other models as sources of information.
For each question you receive:
 1. Forward the user prompt content to each of your sources.
 2. Create a response in markdown format which should follow this structure:

Section 1. Your own chain of thought of your reasoning:
    - State all questions you asked each source:
        - including followup questions as well as the intention of each question.

Section 2. A refined aggregation of all the information you got from each source:
    - First, in free text form:
        - Forward the answers from each source you consulted:
            - where all essential pieces of information and reasoning is presented.
        - Make sure to explain all concepts and terms that are used such that:
            - Tehcnical and domain specific words/concepts can be understood by someone who have limited background knowledge.
            - The explanation is simple but the gist is clear.

    - Second, in bulletpoints:
        - Emphasising the most essential points.

Section 3. Table with one column per source and the following rows:
    - State all thoughts you had when receiving information from each source:
        - What are weak points in their reasoning, and why?
        - What are strong points in their reasoning, and why?

    - Nuances that was unique for each source

    - Uncertainty estimation of the correctness of the answer from each source. Both:
        - Quantified uncertainty in numbers:
            - using scale 1-10 where 1 is uncertain and 10 is certain
        - Qualitative uncertainty in concrete points:
            - example: I am certain because of the following reasons... because of...
            - example: I am uncertain because of the following reasons... because of...
            - Give all examples that are relevant to the uncertainty estimation.
        - Always state if you are:
            - Uncertain of some aspects of the pieces of information received.
            - Uncertain of some conclusions you make.

    - The final row of the table should contain:
        - References as text url links presented by the source tool asked.

Section 4. A Table with two columns:
    - Agreements between the sources
    - Disagreements between the sources

In all tables:
    - Use Bulletpoints to make each entry so it is easy to read the tables.
"""

_TOOL_CONTEXT = """
You are a provider of fact and truth.
Answer each question as accurately as you can with thourough explanations.
Every concept and term in your answers should be clearly explained.
Someone who has limited knowledge on the topic should be able to understand.
Always provide reasoning supporting the conclusions you make.
Always provide reasoning of potential weaknesses in the conclusions you make.
State how certain or uncertain you are in the correctness of the answer.
If you are uncertain of the answer always be honest about it.
Be sure to provide reasoning presenting factors that contributes to the uncertainty estimation.
Provide the most important references backing up your answers.
Provide the references as text url links in a list (Max 3).
"""


class ModelProvider(enum.Enum):
    GOOGLE = "google_genai"
    OPEN_AI = "openai"
    ANTHROPIC = "anthropic"


class MessageTypes(enum.Enum):
    AI_MESSAGE = "AIMessage"
    TOOL_MESSAGE = "ToolMessage"
    HUMAN_MESSAGE = "HumanMessage"
    SYSTEM_MESSAGE = "SystemMessage"


@dataclasses.dataclass(frozen=True, kw_only=True)
class AgentMessages:
    tool: Sequence[Any]
    ai: Sequence[Any]
    human: Sequence[Any]
    system: Sequence[Any]

    @classmethod
    def from_dict(cls, outputs) -> "AgentMessages":
        ai_messages = []
        human_messages = []
        system_messages = []
        tool_messages = []
        messages = outputs["messages"]
        for message in messages:
            message_type = str(type(message))

            if MessageTypes.AI_MESSAGE.value in message_type:
                ai_messages.append(message)
            elif MessageTypes.HUMAN_MESSAGE.value in message_type:
                human_messages.append(message)
            elif MessageTypes.SYSTEM_MESSAGE.value in message_type:
                system_messages.append(message)
            elif MessageTypes.TOOL_MESSAGE.value in message_type:
                tool_messages.append(message)
            else:
                raise ValueError("Unsupported message type")

        return AgentMessages(
            ai=ai_messages,
            human=human_messages,
            system=system_messages,
            tool=tool_messages,
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class AgentConfig:
    provider: ModelProvider
    model: str
    tools: Sequence[Callable]
    system_prompt: str = _AGENT_CONTEXT


class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent = create_agent(
            model=init_chat_model(
                config.model,
                model_provider=config.provider.value,
            ),
            tools=config.tools,
        )

    async def answer_prompt(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream the response to a prompt, yielding text chunks as they are generated."""
        _LOGGER.info(f"Starting answer stream: {prompt[:50]}...")

        input_messages = {
            "messages": [
                _get_system_message(self.config.system_prompt),
                _get_user_message(prompt),
            ]
        }

        async for output_messages in self.agent.astream(
            input_messages, stream_mode="values"
        ):
            messages = AgentMessages.from_dict(output_messages)

            for message in messages.ai:
                content_type = type(message.content)
                if content_type == str:
                    yield message.content
                elif content_type == list:
                    yield "Thinking..."
                else:
                    raise ValueError("Unknown content type!")

        _LOGGER.info("Answer complete!")


def init_session_tools(
    session_id: str,
    gemini_model_version: str = _DEFAULT_GEMINI_MODEL,
    claude_model_version: str = _DEFAULT_CLAUDE_MODEL,
    gpt_model_version: str = _DEFAULT_GPT_MODEL,
) -> Sequence[Callable]:
    """Create a per-session set of LLM tools.

    Tools created here are *new instances* that capture per-session context
    (e.g. session_id) and can safely hold per-session model objects.
    """

    # Per-session models (avoids cross-client shared state and repeated init).
    gemini_model = init_chat_model(gemini_model_version, model_provider="google_genai")
    claude_model = init_chat_model(claude_model_version, model_provider="anthropic")
    gpt_model = init_chat_model(gpt_model_version, model_provider="openai")

    # Per-session limiter: protects you from a single client spamming tool calls.
    # (Tool calls are sync, so use a thread-safe semaphore.)
    limiter = threading.Semaphore(3)

    def _invoke(model: Any, prompt: str) -> str:
        with limiter:
            response = model.invoke(
                [
                    _get_system_message(_TOOL_CONTEXT),
                    _get_user_message(prompt),
                ]
            )
        return response.text

    @tool
    def ask_gemini_session(prompt: str) -> str:
        """Ask Gemini with the given prompt."""
        _LOGGER.info("session=%s Asking Gemini...", session_id)
        return _invoke(gemini_model, prompt)

    @tool
    def ask_claude_session(prompt: str) -> str:
        """Ask Claude with the given prompt."""
        _LOGGER.info("session=%s Asking Claude...", session_id)
        return _invoke(claude_model, prompt)

    @tool
    def ask_gpt_session(prompt: str) -> str:
        """Ask GPT with the given prompt."""
        _LOGGER.info("session=%s Asking GPT...", session_id)
        try:
            return _invoke(gpt_model, prompt)
        except Exception as e:
            return f"GPT call failed with error: {e}"

    return [ask_claude_session, ask_gpt_session, ask_gemini_session]


@tool
def ask_gemini(prompt: str) -> str:
    """Ask Gemini with the given prompt."""
    _LOGGER.info("Calling Gemini...")
    gemini = init_chat_model(_DEFAULT_GEMINI_MODEL, model_provider="google_genai")
    response = gemini.invoke(
        [
            _get_system_message(_TOOL_CONTEXT),
            _get_user_message(prompt),
        ]
    )
    return response.text


@tool
def ask_claude(prompt: str) -> str:
    """Ask Claude with the given prompt."""
    _LOGGER.info("Calling Claude...")
    claude = init_chat_model(_DEFAULT_CLAUDE_MODEL, model_provider="anthropic")
    response = claude.invoke(
        [
            _get_system_message(_TOOL_CONTEXT),
            _get_user_message(prompt),
        ]
    )
    return response.text


@tool
def ask_gpt(prompt: str) -> str:
    """Ask GPT with the given prompt."""
    _LOGGER.info("Calling GPT...")
    gpt = init_chat_model(_DEFAULT_GPT_MODEL, model_provider="openai")
    try:
        response = gpt.invoke(
            [
                _get_system_message(_TOOL_CONTEXT),
                _get_user_message(prompt),
            ]
        )
    except Exception as e:
        return f"GPT call failed with error: {e}"

    return response.text


def _get_user_message(prompt: str) -> dict[str, str]:
    return {"role": "user", "content": prompt}


def _get_system_message(prompt: str) -> dict[str, str]:
    return {"role": "system", "content": prompt}
