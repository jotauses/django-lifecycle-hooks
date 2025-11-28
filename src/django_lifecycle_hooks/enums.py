from enum import StrEnum, auto


class HookType(StrEnum):
    """
    Defines the available lifecycle trigger points.
    Using StrEnum (Python 3.11+) allows for fast string comparisons.
    """

    BEFORE_SAVE = auto()
    AFTER_SAVE = auto()
    BEFORE_CREATE = auto()
    AFTER_CREATE = auto()
    BEFORE_UPDATE = auto()
    AFTER_UPDATE = auto()
    BEFORE_DELETE = auto()
    AFTER_DELETE = auto()
