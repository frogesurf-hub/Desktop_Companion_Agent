from pathlib import Path


class CharacterSystemError(Exception):
    """
    Character System 公共错误的基础类型。
    """


class CharacterDefinitionLoadError(CharacterSystemError):
    """
    Character Definition 文件无法解析为合法领域对象。
    """

    def __init__(
        self,
        path: Path,
        reason: str,
    ) -> None:
        self.path = path

        super().__init__(
            f"Failed to load Character definition "
            f"from {path}: {reason}"
        )


class DuplicateCharacterIdError(CharacterSystemError):
    """
    多个 Character Definition 使用了相同 character_id。
    """

    def __init__(
        self,
        character_id: str,
    ) -> None:
        self.character_id = character_id

        super().__init__(
            f"Duplicate Character ID: {character_id}"
        )


class CharacterNotFoundError(CharacterSystemError):
    """
    指定 character_id 不存在于已加载 Character 集合中。
    """

    def __init__(
        self,
        character_id: str,
    ) -> None:
        self.character_id = character_id

        super().__init__(
            f"Character not found: {character_id}"
        )
