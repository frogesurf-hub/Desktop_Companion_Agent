from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class PreparedMemoryContext:
    """
    已完成 Retrieval 的 factual Memory 上下文。

    保持各 Memory Domain 的语义边界，
    供后续 PromptContextComposer 消费。
    """

    user_profile: tuple[str, ...] = ()
    working_context: tuple[str, ...] = ()
    relevant_episodes: tuple[str, ...] = ()
    relationship_context: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        """
        当前上下文是否完全不包含可用 Memory。
        """

        return not any(
            (
                self.user_profile,
                self.working_context,
                self.relevant_episodes,
                self.relationship_context,
            )
        )
