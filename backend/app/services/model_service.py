import os
import json
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

MODEL_NAME = os.getenv("OLLAMA_MODEL", "mridiot918/qwen3.6-27b-uncensored")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "60"))
DEFAULT_NUM_PREDICT = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9


@dataclass(frozen=True)
class GenerationOptions:
    model_name: str
    num_predict: int
    temperature: float
    top_p: float


async def stream_model(
    history: Sequence[dict[str, str]],
    options: GenerationOptions,
) -> AsyncIterator[str]:
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
        reasoning=True,
    )
    async for chunk in model.astream(messages):
        if not isinstance(chunk.content, str):
            raise TypeError("Ollama returned a non-text response.")
        if chunk.content:
            yield chunk.content


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
