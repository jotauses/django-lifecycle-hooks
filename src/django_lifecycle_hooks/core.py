from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, eq=False, order=False)
class HookConfig:
    """
    Immutable configuration for a single hook execution.
    'slots=True' ensures minimal memory footprint per hook instance.
    'eq=False' and 'order=False' remove overhead of unnecessary dunder methods.
    """

    method_name: str
    when: str | None
    was: Any
    is_now: Any
    has_changed: bool
    on_commit: bool


class LifecycleRegistry:
    """
    Parses and holds the lifecycle configuration for a Model class.
    This logic runs ONCE per class definition (Import time), ensuring
    near-zero overhead during Runtime requests.
    """

    __slots__ = ("_hooks", "_watched_fields")

    def __init__(self, model_cls: type) -> None:
        self._hooks: dict[str, list[HookConfig]] = defaultdict(list)
        self._watched_fields: set[str] = set()
        self._parse_hooks(model_cls)

    def _parse_hooks(self, model_cls: type) -> None:
        # Iterate over class dictionary to find decorated methods.
        # We look specifically at the class dict to avoid aggressive MRO scans
        # that might duplicate inherited hooks confusingly.
        for name, attr in model_cls.__dict__.items():
            if meta := getattr(attr, "_lifecycle_meta", None):
                config = HookConfig(
                    method_name=name,
                    when=meta["when"],
                    was=meta["was"],
                    is_now=meta["is_now"],
                    has_changed=meta["has_changed"],
                    on_commit=meta["on_commit"],
                )

                self._hooks[meta["trigger"]].append(config)

                # Track monitored fields to limit snapshot size
                if meta["when"]:
                    self._watched_fields.add(meta["when"])

    def get_hooks(self, trigger: str) -> list[HookConfig]:
        """Retrieve pre-computed hooks for a specific trigger."""
        return self._hooks[trigger]

    @property
    def watched_fields(self) -> set[str]:
        """Return the set of fields that require value snapshots."""
        return self._watched_fields
