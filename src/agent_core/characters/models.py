from dataclasses import dataclass


def _require_non_blank_text(
    field_name: str,
    value: str,
) -> None:
    """
    验证 Character 必填文本字段包含实际内容。
    """

    if not value.strip():
        raise ValueError(
            f"CharacterDefinition {field_name} must not be empty"
        )


def _validate_optional_text(
    field_name: str,
    value: str | None,
) -> None:
    """
    验证 Character 可选文本字段。

    None 表示该部分未定义；
    若显式提供文本，则必须包含实际内容。
    """

    if value is not None and not value.strip():
        raise ValueError(
            f"CharacterDefinition {field_name} "
            "must not be empty when provided"
        )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class CharacterDefinition:
    """
    Character System 的稳定角色定义。

    这里只保存相对稳定的角色身份与表达特征，
    不包含 Memory、Internal State、权限或运行时真实状态。
    """

    character_id: str
    display_name: str
    identity: str
    persona: str
    speech_style: str
    preferences: str | None = None
    core_values: str | None = None
    fictional_background: str | None = None

    def __post_init__(self) -> None:
        """
        验证 Character Definition 的最小领域约束。
        """

        _require_non_blank_text(
            "character_id",
            self.character_id,
        )
        _require_non_blank_text(
            "display_name",
            self.display_name,
        )
        _require_non_blank_text(
            "identity",
            self.identity,
        )
        _require_non_blank_text(
            "persona",
            self.persona,
        )
        _require_non_blank_text(
            "speech_style",
            self.speech_style,
        )

        _validate_optional_text(
            "preferences",
            self.preferences,
        )
        _validate_optional_text(
            "core_values",
            self.core_values,
        )
        _validate_optional_text(
            "fictional_background",
            self.fictional_background,
        )
