class EventSystemError(Exception):
    """
    Event System 公共契约错误的基础类型。
    """


class EventBusStateError(EventSystemError):
    """
    Event Bus 操作与当前生命周期状态不兼容。
    """


class EventBusFullError(EventSystemError):
    """
    Event Bus bounded queue 已满，Event 未被接受。
    """
