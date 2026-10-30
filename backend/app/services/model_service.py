import os
import json
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_ollama import ChatOllama

from app.tools.customization import CUSTOMIZATION_TOOLS, GUIDANCE_SAVED_MESSAGE

MODEL_NAME = os.getenv("OLLAMA_MODEL", "mridiot918/qwen3.6-27b-uncensored")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "60"))
DEFAULT_NUM_PREDICT = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_REPEAT_PENALTY = 1.05
DEFAULT_REASONING = True
MAX_TOOL_ROUNDS = 3


@dataclass(frozen=True)
class GenerationOptions:
    model_name: str
    num_predict: int
    temperature: float
    top_p: float
    repeat_penalty: float = DEFAULT_REPEAT_PENALTY
    reasoning: bool = DEFAULT_REASONING


@dataclass(frozen=True)
class GuidanceSavedEvent:
    pass


ModelStreamEvent = str | GuidanceSavedEvent


async def stream_model(
    history: Sequence[dict[str, str]],
    options: GenerationOptions,
) -> AsyncIterator[ModelStreamEvent]:
    messages: list[BaseMessage] = [
        {
            "user": HumanMessage,
            "assistant": AIMessage,
            "system": SystemMessage,
        }[item["role"]](content=item["content"])
        for item in history
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
    ).bind_tools(CUSTOMIZATION_TOOLS)
    available_tools = {item.name: item for item in CUSTOMIZATION_TOOLS}

    for tool_round in range(MAX_TOOL_ROUNDS + 1):
        complete_chunk = None
        async for chunk in model.astream(messages):
            if not isinstance(chunk.content, str):
                raise TypeError("Ollama returned a non-text response.")
            complete_chunk = (
                chunk if complete_chunk is None else complete_chunk + chunk
            )
            if chunk.content:
                yield chunk.content

        tool_calls = complete_chunk.tool_calls if complete_chunk is not None else []
        if not tool_calls:
            return
        if tool_round == MAX_TOOL_ROUNDS:
            raise RuntimeError("The model exceeded the maximum number of tool calls.")

        messages.append(
            AIMessage(
                content=complete_chunk.content,
                tool_calls=tool_calls,
            )
        )
        for tool_call in tool_calls:
            tool = available_tools.get(tool_call["name"])
            if tool is None:
                raise RuntimeError(f"The model requested an unknown tool: {tool_call['name']}.")
            result = await tool.ainvoke(tool_call["args"])
            if (
                tool_call["name"] == "remember_guidance"
                and result == GUIDANCE_SAVED_MESSAGE
            ):
                yield GuidanceSavedEvent()
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )


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
