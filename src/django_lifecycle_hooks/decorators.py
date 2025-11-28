from functools import wraps
from typing import Any, Callable

from .enums import HookType


def hook(
    trigger: HookType,
    when: str | None = None,
    was: Any = "*",
    is_now: Any = "*",
    has_changed: bool = False,
    on_commit: bool = False,
) -> Callable[[Any], Any]:
    """
    Decorator to mark a method as a lifecycle hook.

    It attaches a strict metadata dictionary to the function object,
    which is later read by the LifecycleRegistry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(
            func,
            "_lifecycle_meta",
            {
                "trigger": trigger,
                "when": when,
                "was": was,
                "is_now": is_now,
                "has_changed": has_changed,
                "on_commit": on_commit,
            },
        )

        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
