from dataclasses import FrozenInstanceError

import pytest

from agent_core.characters import CharacterDefinition


def _create_character() -> CharacterDefinition:
    """
    创建 Character domain 测试使用的完整有效定义。
    """

    return CharacterDefinition(
        character_id="aria",
        display_name="Aria",
        identity="A desktop AI companion.",
        persona="Cheerful and playful.",
        speech_style="Natural, familiar, and lightly teasing.",
        preferences="Music and lyrical things.",
        core_values="Values honesty and curiosity.",
        fictional_background="A fictional background for testing.",
    )


def test_character_definition_preserves_domain_content() -> None:
    """
    验证 Character Definition 保留各语义部分。
    """

    character = _create_character()

    assert character.character_id == "aria"
    assert character.display_name == "Aria"
    assert character.identity == "A desktop AI companion."
    assert character.persona == "Cheerful and playful."
    assert (
        character.speech_style
        == "Natural, familiar, and lightly teasing."
    )
    assert character.preferences == "Music and lyrical things."
    assert character.core_values == "Values honesty and curiosity."
    assert (
        character.fictional_background
        == "A fictional background for testing."
    )


def test_character_definition_allows_optional_sections_to_be_absent() -> None:
    """
    验证非核心 Character 内容可以不存在。
    """

    character = CharacterDefinition(
        character_id="minimal",
        display_name="Minimal",
        identity="A test companion.",
        persona="Calm.",
        speech_style="Concise.",
    )

    assert character.preferences is None
    assert character.core_values is None
    assert character.fictional_background is None


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    [
        (
            "character_id",
            {"character_id": "   "},
        ),
        (
            "display_name",
            {"display_name": "   "},
        ),
        (
            "identity",
            {"identity": "   "},
        ),
        (
            "persona",
            {"persona": "   "},
        ),
        (
            "speech_style",
            {"speech_style": "   "},
        ),
    ],
)
def test_character_definition_rejects_blank_required_content(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    """
    验证 Character 必填字段不能是空白文本。
    """

    values = {
        "character_id": "aria",
        "display_name": "Aria",
        "identity": "A desktop AI companion.",
        "persona": "Cheerful.",
        "speech_style": "Natural.",
    }
    values.update(overrides)

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be empty",
    ):
        CharacterDefinition(
            character_id=values["character_id"],
            display_name=values["display_name"],
            identity=values["identity"],
            persona=values["persona"],
            speech_style=values["speech_style"],
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "preferences",
        "core_values",
        "fictional_background",
    ],
)
def test_character_definition_rejects_blank_optional_content(
    field_name: str,
) -> None:
    """
    验证显式提供的可选 Character 内容不能只是空白文本。
    """

    optional_values: dict[str, str | None] = {
        "preferences": None,
        "core_values": None,
        "fictional_background": None,
    }
    optional_values[field_name] = "   "

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be empty when provided",
    ):
        CharacterDefinition(
            character_id="aria",
            display_name="Aria",
            identity="A desktop AI companion.",
            persona="Cheerful.",
            speech_style="Natural.",
            preferences=optional_values["preferences"],
            core_values=optional_values["core_values"],
            fictional_background=optional_values[
                "fictional_background"
            ],
        )


def test_character_definition_is_immutable() -> None:
    """
    验证 Character Definition 创建后不可原地修改。
    """

    character = _create_character()

    with pytest.raises(
        FrozenInstanceError,
    ):
        setattr(
            character,
            "persona",
            "changed",
        )
