from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from django.db import models


@dataclass(frozen=True, slots=True, eq=False, order=False)
class HookConfig:
    """
    Immutable configuration for a single hook execution.

    Attributes:
        method_name: Name of the method to execute.
        when: Field name to watch (optional).
        was: Previous value to match (optional).
        is_now: Current value to match (optional).
        has_changed: Whether to check if the field has changed.
        condition: Advanced condition object (optional).
        priority: Execution priority (higher runs first).
        on_commit: Whether to run after transaction commit.
        is_async: Whether the hook method is a coroutine.
    """

    method_name: str
    when: str | None
    was: Any
    is_now: Any
    has_changed: bool
    condition: Any
    priority: int
    on_commit: bool
    is_async: bool


class LifecycleRegistry:
    """
    Parses and holds the lifecycle configuration for a Model class.

    This logic runs ONCE per class definition (Import time), ensuring
    near-zero overhead during Runtime requests.
    """

    __slots__ = ("_hooks", "_watched_fields")

    def __init__(self, model_cls: type[models.Model]) -> None:
        self._hooks: dict[str, list[HookConfig]] = defaultdict(list)
        self._watched_fields: set[str] = set()
        self._parse_hooks(model_cls)

    def _parse_hooks(self, model_cls: type[models.Model]) -> None:
        """
        Parses the hooks from the model class and populates the registry.
        """
        # Iterate over class dictionary to find decorated methods.
        # We look specifically at the class dict to avoid aggressive MRO scans
        # that might duplicate inherited hooks confusingly.
        for name, attr in model_cls.__dict__.items():
            if meta_list := getattr(attr, "_lifecycle_meta", None):
                for meta in meta_list:
                    config = HookConfig(
                        method_name=name,
                        when=meta["when"],
                        was=meta["was"],
                        is_now=meta["is_now"],
                        has_changed=meta["has_changed"],
                        condition=meta["condition"],
                        priority=meta["priority"],
                        on_commit=meta["on_commit"],
                        is_async=meta["is_async"],
                    )

                    self._hooks[meta["trigger"]].append(config)
                    # Sort by priority descending (higher priority runs first)
                    self._hooks[meta["trigger"]].sort(
                        key=lambda x: x.priority, reverse=True
                    )

                    # Track monitored fields to limit snapshot size
                    if meta["when"]:
                        self._watched_fields.add(meta["when"])

                    if meta["condition"]:
                        self._watched_fields.update(
                            self._extract_fields_from_condition(meta["condition"])
                        )

    def _extract_fields_from_condition(self, condition: Any) -> set[str]:
        """
        Recursively extracts field names from a condition object.
        """
        fields = set()
        if hasattr(condition, "field_name"):
            fields.add(condition.field_name)

        # Handle And/Or/Not conditions
        if hasattr(condition, "c1"):
            fields.update(self._extract_fields_from_condition(condition.c1))
        if hasattr(condition, "c2"):
            fields.update(self._extract_fields_from_condition(condition.c2))
        if hasattr(condition, "c"):  # NotCondition
            fields.update(self._extract_fields_from_condition(condition.c))

        return fields

    def get_hooks(self, trigger: str) -> list[HookConfig]:
        """Retrieve pre-computed hooks for a specific trigger."""
        return self._hooks[trigger]

    @property
    def watched_fields(self) -> set[str]:
        """Return the set of fields that require value snapshots."""
        return self._watched_fields
