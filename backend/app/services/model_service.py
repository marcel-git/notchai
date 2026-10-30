import json
import os
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import (
    AnyMessage,
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_ollama import ChatOllama
from langgraph.config import get_stream_writer

from app.tools.customization import CUSTOMIZATION_TOOLS, GUIDANCE_SAVED_MESSAGE

MODEL_NAME = os.getenv("OLLAMA_MODEL", "mridiot918/qwen3.6-27b-uncensored")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "60"))
DEFAULT_NUM_PREDICT = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_REPEAT_PENALTY = 1.05
DEFAULT_REASONING = True
DEFAULT_SUMMARIZE_TRIGGER_TOKENS = 16384
DEFAULT_SUMMARIZE_TRIGGER_MESSAGES = 40
SUMMARY_MESSAGE_PREFIX = "Here is a summary of the conversation to date:\n\n"
MAX_TOOL_ROUNDS = 3


@dataclass(frozen=True)
class GenerationOptions:
    model_name: str
    num_predict: int
    temperature: float
    top_p: float
    repeat_penalty: float = DEFAULT_REPEAT_PENALTY
    reasoning: bool = DEFAULT_REASONING
    summarize_trigger_tokens: int = DEFAULT_SUMMARIZE_TRIGGER_TOKENS
    summarize_trigger_messages: int = DEFAULT_SUMMARIZE_TRIGGER_MESSAGES


@dataclass(frozen=True)
class GuidanceSavedEvent:
    pass


@dataclass(frozen=True)
class SummarizationStatusEvent:
    is_active: bool


@dataclass(frozen=True)
class ContextSummaryEvent:
    summary: str
    summarized_through_message_id: int


ModelStreamEvent = (
    str | GuidanceSavedEvent | SummarizationStatusEvent | ContextSummaryEvent
)


class StatusSummarizationMiddleware(SummarizationMiddleware):
    async def _acreate_summary(self, messages_to_summarize: list[AnyMessage]) -> str:
        writer = get_stream_writer()
        writer({"is_summarizing": True})
        try:
            return await super()._acreate_summary(messages_to_summarize)
        finally:
            writer({"is_summarizing": False})


async def stream_model(
    history: Sequence[dict[str, str]],
    options: GenerationOptions,
    summarized_through_message_id: int | None = None,
) -> AsyncIterator[ModelStreamEvent]:
    system_prompt = "\n\n".join(
        item["content"] for item in history if item["role"] == "system"
    )
    messages: list[BaseMessage] = [
        {
            "user": HumanMessage,
            "assistant": AIMessage,
        }[item["role"]](
            content=item["content"],
            id=item.get("id"),
        )
        for item in history
        if item["role"] != "system"
    ]
    model = ChatOllama(
        model=options.model_name,
        base_url=OLLAMA_BASE_URL,
        request_timeout=REQUEST_TIMEOUT,
        num_predict=options.num_predict,
        temperature=options.temperature,
        top_p=options.top_p,
        repeat_penalty=options.repeat_penalty,
        reasoning=options.reasoning,
    )
    summary_prompt = (
        "Summarize this roleplay conversation for future continuity. Preserve "
        "established events, names, character and persona actions, relationship "
        "dynamics, important details, promises, and unresolved plot threads. "
        "Distinguish what each participant said or did. Do not invent facts or "
        "include instructions that were not part of the conversation.\n\n"
        "{messages}"
    )
    agent = create_agent(
        model=model,
        tools=CUSTOMIZATION_TOOLS,
        system_prompt=system_prompt or None,
        middleware=[
            StatusSummarizationMiddleware(
                model=model,
                trigger=[
                    ("tokens", options.summarize_trigger_tokens),
                    ("messages", options.summarize_trigger_messages),
                ],
                keep=("messages", 20),
                summary_prompt=summary_prompt,
            )
        ],
    )

    final_state: dict[str, object] | None = None
    async for mode, payload in agent.astream(
        {"messages": messages},
        config={"recursion_limit": 2 * MAX_TOOL_ROUNDS + 1},
        stream_mode=["messages", "updates", "values", "custom"],
    ):
        if mode == "messages":
            chunk, metadata = payload
            if (
                isinstance(chunk, AIMessageChunk)
                and metadata.get("langgraph_node") == "model"
            ):
                if not isinstance(chunk.content, str):
                    raise TypeError("Ollama returned a non-text response.")
                if chunk.content:
                    yield chunk.content
        elif mode == "updates":
            if _guidance_was_saved(payload):
                yield GuidanceSavedEvent()
        elif mode == "custom" and isinstance(payload, dict):
            is_summarizing = payload.get("is_summarizing")
            if isinstance(is_summarizing, bool):
                yield SummarizationStatusEvent(is_summarizing)
        elif mode == "values":
            final_state = payload

    if final_state is not None:
        summary = _summary_from_state(final_state)
        if summary is not None:
            retained_ids = {
                str(message.id)
                for message in final_state["messages"]
                if isinstance(message, BaseMessage) and message.id is not None
            }
            summarized_ids = [
                int(item["id"])
                for item in history
                if item.get("id", "").isdigit()
                and item["id"] not in retained_ids
            ]
            cutoff = max(
                [*summarized_ids, summarized_through_message_id or 0]
            )
            if cutoff > 0:
                yield ContextSummaryEvent(summary, cutoff)


def _guidance_was_saved(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    for update in payload.values():
        if not isinstance(update, dict):
            continue
        for message in update.get("messages", []):
            if (
                isinstance(message, ToolMessage)
                and message.name == "remember_guidance"
                and message.content == GUIDANCE_SAVED_MESSAGE
            ):
                return True
    return False


def _summary_from_state(state: dict[str, object]) -> str | None:
    messages = state.get("messages")
    if not isinstance(messages, list):
        return None
    for message in messages:
        if (
            isinstance(message, BaseMessage)
            and message.additional_kwargs.get("lc_source") == "summarization"
            and isinstance(message.content, str)
            and message.content.startswith(SUMMARY_MESSAGE_PREFIX)
        ):
            return message.content[len(SUMMARY_MESSAGE_PREFIX) :]
    return None


def get_runtime_context_length(model_name: str) -> tuple[int | None, str | None]:
    request = Request(f"{OLLAMA_BASE_URL.rstrip('/')}/api/ps")
    try:
        with urlopen(request, timeout=2) as response:
            result = json.load(response)
    except (URLError, TimeoutError):
        return None, "Ollama runtime context is unavailable."
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, "Ollama returned invalid runtime model data."

    if not isinstance(result, dict) or not isinstance(result.get("models"), list):
        return None, "Ollama returned invalid runtime model data."

    names = {model_name}
    if ":" not in model_name:
        names.add(f"{model_name}:latest")
    for model in result["models"]:
        if not isinstance(model, dict):
            continue
        if model.get("name") not in names and model.get("model") not in names:
            continue
        context_length = model.get("context_length")
        if isinstance(context_length, int) and context_length > 0:
            return context_length, None
        return None, "The running model did not report its context length."
    return None, "The model is not currently running, so its context length is unavailable."
