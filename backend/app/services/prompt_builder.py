from collections.abc import Sequence

from app.models.conversation import Character, Persona

GUIDANCE_HEADER = "Global user guidance:"


def build_guidance_section(guidance: Sequence[str]) -> str:
    return "\n".join(
        [
            GUIDANCE_HEADER,
            "Follow these explicit, lasting user preferences in every conversation:",
            *[f"- {item}" for item in guidance],
        ]
    )


def strip_guidance_section(
    system_prompt: str,
    guidance: Sequence[str],
) -> str:
    if not guidance:
        return system_prompt
    section = f"\n\n{build_guidance_section(guidance)}"
    if system_prompt.endswith(section):
        return system_prompt[: -len(section)]
    return system_prompt


def build_system_prompt(
    character: Character | None,
    persona: Persona | None,
) -> str:
    if character is None and persona is None:
        return ""

    sections = ["Play the selected character as the agent."]
    if character is not None:
        sections.extend(
            [
                "",
                "Character:",
                f"Name: {character.name}",
                f"Description: {character.description}",
                f"Personality: {character.personality}",
                f"Background: {character.background}",
                f"Custom instructions: {character.custom_instructions}",
            ]
        )
    if persona is not None:
        sections.extend(
            [
                "",
                "Persona played by the user:",
                f"Name: {persona.name}",
                f"Identity: {persona.identity}",
                f"Appearance: {persona.appearance}",
                f"Background: {persona.background}",
                f"Behavior: {persona.behavior}",
            ]
        )
    elif character is not None:
        sections.extend(
            [
                "",
                "Persona played by the user:",
                "Name: Stranger",
                "Identity: The user is acting as themselves without a selected persona profile.",
            ]
        )
    sections.extend(
        [
            "",
            "Stay consistent with the character you are playing. Treat the persona "
            "as the role and identity the user is acting as; do not speak or act "
            "for the persona.",
        ]
    )
    return "\n".join(sections)


def build_prompt(
    character: Character | None,
    persona: Persona | None,
    history: Sequence[dict[str, str]],
    system_prompt: str | None = None,
    guidance: Sequence[str] = (),
) -> list[dict[str, str]]:
    if system_prompt is None:
        system_prompt = build_system_prompt(character, persona)
    if guidance:
        guidance_section = build_guidance_section(guidance)
        system_prompt = (
            f"{system_prompt}\n\n{guidance_section}"
            if system_prompt
            else guidance_section
        )
    if not system_prompt:
        return list(history)
    return [{"role": "system", "content": system_prompt}, *history]
