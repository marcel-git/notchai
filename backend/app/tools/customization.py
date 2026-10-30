from langchain_core.tools import tool

from app.db.customization import add_guidance, get_guidance_entries, remove_guidance

GUIDANCE_SAVED_MESSAGE = "Guidance saved for all conversations."


@tool
def remember_guidance(guidance: str) -> str:
    """Save a concise, lasting global rule for how to behave in future chats.

    Use this when the user explicitly states a lasting preference or behavior
    rule, including direct requests such as "from now on". Do not infer
    preferences from feedback, and do not save story events, character details,
    or temporary requests.
    """
    try:
        return add_guidance(guidance)
    except ValueError as error:
        return str(error)


@tool
def list_guidance_tool() -> str:
    """List the user's saved global behavior guidance when asked what is remembered."""
    entries = get_guidance_entries()
    if not entries:
        return "No global user guidance is saved."
    return "\n".join(f"{item['id']}: {item['text']}" for item in entries)


@tool
def forget_guidance(guidance_id: int) -> str:
    """Remove a saved global guidance entry when the user asks you to forget it."""
    if remove_guidance(guidance_id):
        return "Guidance removed."
    return f"No saved guidance entry has id {guidance_id}."


CUSTOMIZATION_TOOLS = [remember_guidance, list_guidance_tool, forget_guidance]
