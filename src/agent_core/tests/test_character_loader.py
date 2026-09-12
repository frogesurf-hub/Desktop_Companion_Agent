from pathlib import Path

import pytest

from agent_core.characters import (
    CharacterDefinitionLoadError,
    CharacterNotFoundError,
    DuplicateCharacterIdError,
    load_character_definition,
    load_character_definitions,
    resolve_character,
)


def _write_character(
    path: Path,
    *,
    character_id: str = "aria",
) -> None:
    """
    写入 Character loader 测试使用的合法 TOML。
    """

    path.write_text(
        f'''
character_id = "{character_id}"
display_name = "Aria"

[identity]
description = """
A desktop AI companion.
"""

[persona]
description = """
Cheerful and playful.
"""

[speech_style]
description = """
Natural and familiar.
"""

[preferences]
description = """
Music.
"""
'''.strip(),
        encoding="utf-8",
    )


def test_load_character_definition_from_toml(
    tmp_path: Path,
) -> None:
    """
    验证合法 TOML 会转换为 CharacterDefinition。
    """

    path = tmp_path / "aria.toml"
    _write_character(
        path,
    )

    character = load_character_definition(
        path,
    )

    assert character.character_id == "aria"
    assert character.display_name == "Aria"
    assert (
        character.identity
        == "A desktop AI companion.\n"
    )
    assert character.persona == "Cheerful and playful.\n"
    assert character.speech_style == "Natural and familiar.\n"
    assert character.preferences == "Music.\n"
    assert character.core_values is None
    assert character.fictional_background is None


def test_load_character_definition_rejects_malformed_toml(
    tmp_path: Path,
) -> None:
    """
    验证语法错误的 TOML 会通过 Character loader 边界失败。
    """

    path = tmp_path / "broken.toml"
    path.write_text(
        'character_id = "broken',
        encoding="utf-8",
    )

    with pytest.raises(
        CharacterDefinitionLoadError,
    ):
        load_character_definition(
            path,
        )


def test_load_character_definition_rejects_unknown_top_level_field(
    tmp_path: Path,
) -> None:
    path = tmp_path / "aria.toml"

    path.write_text(
        '''
character_id = "aria"
display_name = "Aria"
unknown_field = "value"

[identity]
description = """
A desktop AI companion.
"""

[persona]
description = """
Cheerful and playful.
"""

[speech_style]
description = """
Natural and familiar.
"""
'''.strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        CharacterDefinitionLoadError,
        match="Unknown field in Character definition",
    ):
        load_character_definition(path)


def test_load_character_definition_rejects_unknown_section_field(
    tmp_path: Path,
) -> None:
    """
    验证 Character section 内的未知字段不会被静默忽略。
    """

    path = tmp_path / "aria.toml"
    _write_character(
        path,
    )

    content = path.read_text(
        encoding="utf-8",
    )

    path.write_text(
        content + '\nunknown_field = "value"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        CharacterDefinitionLoadError,
        match="Unknown field in preferences",
    ):
        load_character_definition(
            path,
        )


def test_load_character_definition_wraps_domain_validation_error(
    tmp_path: Path,
) -> None:
    """
    验证非法领域内容会通过 Character loader 错误边界失败。
    """

    path = tmp_path / "aria.toml"
    _write_character(
        path,
        character_id="   ",
    )

    with pytest.raises(
        CharacterDefinitionLoadError,
        match="character_id must not be empty",
    ):
        load_character_definition(
            path,
        )


def test_load_character_definitions_loads_multiple_files(
    tmp_path: Path,
) -> None:
    """
    验证目录 loader 可以加载多个 Character。
    """

    _write_character(
        tmp_path / "aria.toml",
        character_id="aria",
    )
    _write_character(
        tmp_path / "second.toml",
        character_id="second",
    )

    definitions = load_character_definitions(
        tmp_path,
    )

    assert set(definitions) == {
        "aria",
        "second",
    }


def test_load_character_definitions_rejects_duplicate_ids(
    tmp_path: Path,
) -> None:
    """
    验证不同文件不能声明相同 Character ID。
    """

    _write_character(
        tmp_path / "first.toml",
        character_id="duplicate",
    )
    _write_character(
        tmp_path / "second.toml",
        character_id="duplicate",
    )

    with pytest.raises(
        DuplicateCharacterIdError,
        match="duplicate",
    ):
        load_character_definitions(
            tmp_path,
        )


def test_load_character_definitions_rejects_missing_directory(
    tmp_path: Path,
) -> None:
    """
    验证不存在的 Character 目录显式失败。
    """

    missing = tmp_path / "missing"

    with pytest.raises(
        CharacterDefinitionLoadError,
    ):
        load_character_definitions(
            missing,
        )


def test_resolve_character_returns_matching_definition(
    tmp_path: Path,
) -> None:
    """
    验证已加载 Character 可以按 ID 解析。
    """

    _write_character(
        tmp_path / "aria.toml",
    )

    definitions = load_character_definitions(
        tmp_path,
    )

    character = resolve_character(
        definitions,
        "aria",
    )

    assert character is definitions["aria"]


def test_resolve_character_rejects_unknown_id(
    tmp_path: Path,
) -> None:
    """
    验证未知 Character ID 显式失败。
    """

    _write_character(
        tmp_path / "aria.toml",
    )

    definitions = load_character_definitions(
        tmp_path,
    )

    with pytest.raises(
        CharacterNotFoundError,
        match="missing",
    ):
        resolve_character(
            definitions,
            "missing",
        )


def test_builtin_aria_definition_loads() -> None:
    """
    验证内置 Aria Character 文件符合当前 schema。
    """

    aria_path = (
        Path(__file__).parents[1]
        / "characters"
        / "definitions"
        / "aria.toml"
    )

    aria = load_character_definition(
        aria_path,
    )

    assert aria.character_id == "aria"
    assert aria.display_name == "Aria"
    assert aria.fictional_background is None
