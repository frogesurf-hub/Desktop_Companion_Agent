import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agent_core.characters.errors import (
    CharacterDefinitionLoadError,
    CharacterNotFoundError,
    DuplicateCharacterIdError,
)
from agent_core.characters.models import CharacterDefinition

_REQUIRED_SECTIONS = (
    "identity",
    "persona",
    "speech_style",
)

_OPTIONAL_SECTIONS = (
    "preferences",
    "core_values",
    "fictional_background",
)

_ALLOWED_TOP_LEVEL_KEYS = {
    "character_id",
    "display_name",
    *_REQUIRED_SECTIONS,
    *_OPTIONAL_SECTIONS,
}

_ALLOWED_SECTION_KEYS = {
    "description",
}


def _require_string(
    data: Mapping[str, Any],
    key: str,
) -> str:
    """
    从 mapping 中读取必填字符串。
    """

    value = data.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f"{key} must be a string"
        )

    return value


def _validate_known_keys(
    data: Mapping[str, Any],
    allowed_keys: set[str],
    context: str,
) -> None:
    """
    拒绝未知字段，避免 Character TOML 拼写错误被静默忽略。
    """

    unknown_keys = set(data) - allowed_keys

    if unknown_keys:
        unknown_key = sorted(unknown_keys)[0]

        raise ValueError(
            f"Unknown field in {context}: {unknown_key}"
        )


def _read_required_section(
    data: Mapping[str, Any],
    section_name: str,
) -> str:
    """
    读取必填 Character section 的 description。
    """

    section = data.get(section_name)

    if not isinstance(section, dict):
        raise ValueError(
            f"{section_name} must be a table"
        )

    _validate_known_keys(
        section,
        _ALLOWED_SECTION_KEYS,
        section_name,
    )

    return _require_string(
        section,
        "description",
    )


def _read_optional_section(
    data: Mapping[str, Any],
    section_name: str,
) -> str | None:
    """
    读取可选 Character section。
    """

    section = data.get(section_name)

    if section is None:
        return None

    if not isinstance(section, dict):
        raise ValueError(
            f"{section_name} must be a table"
        )

    _validate_known_keys(
        section,
        _ALLOWED_SECTION_KEYS,
        section_name,
    )

    return _require_string(
        section,
        "description",
    )


def load_character_definition(
    path: Path,
) -> CharacterDefinition:
    """
    从单个 TOML 文件加载 Character Definition。
    """

    try:
        with path.open("rb") as file:
            data = tomllib.load(file)

        _validate_known_keys(
            data,
            _ALLOWED_TOP_LEVEL_KEYS,
            "Character definition",
        )

        return CharacterDefinition(
            character_id=_require_string(
                data,
                "character_id",
            ),
            display_name=_require_string(
                data,
                "display_name",
            ),
            identity=_read_required_section(
                data,
                "identity",
            ),
            persona=_read_required_section(
                data,
                "persona",
            ),
            speech_style=_read_required_section(
                data,
                "speech_style",
            ),
            preferences=_read_optional_section(
                data,
                "preferences",
            ),
            core_values=_read_optional_section(
                data,
                "core_values",
            ),
            fictional_background=_read_optional_section(
                data,
                "fictional_background",
            ),
        )

    except (
        OSError,
        tomllib.TOMLDecodeError,
        ValueError,
    ) as exc:
        raise CharacterDefinitionLoadError(
            path,
            str(exc),
        ) from exc


def load_character_definitions(
    directory: Path,
) -> dict[str, CharacterDefinition]:
    """
    加载目录中的全部顶层 TOML Character Definition。

    当前 Phase 3 不递归扫描子目录。
    """

    if not directory.is_dir():
        raise CharacterDefinitionLoadError(
            directory,
            "Character definition directory does not exist",
        )

    definitions: dict[
        str,
        CharacterDefinition,
    ] = {}

    for path in sorted(
        directory.glob("*.toml"),
    ):
        character = load_character_definition(
            path,
        )

        if character.character_id in definitions:
            raise DuplicateCharacterIdError(
                character.character_id,
            )

        definitions[
            character.character_id
        ] = character

    return definitions


def resolve_character(
    definitions: Mapping[
        str,
        CharacterDefinition,
    ],
    character_id: str,
) -> CharacterDefinition:
    """
    从已加载 Character 集合中解析指定 Character。
    """

    try:
        return definitions[
            character_id
        ]
    except KeyError as exc:
        raise CharacterNotFoundError(
            character_id,
        ) from exc
