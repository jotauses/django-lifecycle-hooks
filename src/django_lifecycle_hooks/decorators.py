import inspect
from functools import wraps
from typing import Any, Callable

from .enums import HookType


def hook(
    trigger: HookType,
    when: str | None = None,
    was: Any = "*",
    is_now: Any = "*",
    has_changed: bool = False,
    condition: Any = None,
    priority: int = 0,
    on_commit: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to mark a method as a lifecycle hook.

    It attaches a strict metadata dictionary to the function object,
    which is later read by the LifecycleRegistry.

    Args:
        trigger: The lifecycle moment to hook into.
        when: The field name to watch (optional).
        was: The previous value to match (optional).
        is_now: The current value to match (optional).
        has_changed: Whether to trigger only if the field has changed.
        condition: Advanced condition object (optional).
        priority: Execution priority (higher runs first).
        on_commit: Whether to run after transaction commit.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not hasattr(func, "_lifecycle_meta"):
            setattr(func, "_lifecycle_meta", [])

        func._lifecycle_meta.append(
            {
                "trigger": trigger,
                "when": when,
                "was": was,
                "is_now": is_now,
                "has_changed": has_changed,
                "condition": condition,
                "priority": priority,
                "on_commit": on_commit,
                "is_async": inspect.iscoroutinefunction(func),
            }
        )

        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
