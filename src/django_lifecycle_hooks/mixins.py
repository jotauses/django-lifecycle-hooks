from typing import Any

from django.db import models, transaction

from .core import LifecycleRegistry
from .enums import HookType


class LifecycleModelMixin(models.Model):
    """
    High-performance Mixin to add lifecycle hooks capabilities.

    Architecture:
    - Uses __init_subclass__ to build the registry at startup.
    - Uses sparse snapshotting (only copies watched fields).
    - Inlines condition checks for maximum CPU efficiency.
    """

    _lifecycle_registry: LifecycleRegistry

    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Initialize registry once at class creation (Startup)
        cls._lifecycle_registry = LifecycleRegistry(cls)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._lifecycle_initial_state: dict[str, Any] = {}
        self._take_lifecycle_snapshot()

    def _take_lifecycle_snapshot(self) -> None:
        """
        Snapshots only the fields that are actually being watched.
        This reduces memory usage significantly compared to full dict copies.
        """
        if not self.pk:
            return

        registry = self.__class__._lifecycle_registry  # type: ignore

        if not registry.watched_fields:
            return

        for field in registry.watched_fields:
            if hasattr(self, field):
                self._lifecycle_initial_state[field] = getattr(self, field)

    def _run_lifecycle_hooks(self, trigger: HookType) -> None:
        """
        Executes hooks for the given trigger.
        Logic is inlined to avoid function call overhead in tight loops.
        """
        registry = self.__class__._lifecycle_registry  # type: ignore
        hooks = registry.get_hooks(trigger)

        if not hooks:
            return

        initial_state = self._lifecycle_initial_state

        for config in hooks:
            # --- Inline Condition Check ---
            if config.when:
                current_val = getattr(self, config.when, None)
                initial_val = initial_state.get(config.when)

                # Condition: has_changed
                if config.has_changed and current_val == initial_val:
                    continue

                # Condition: was
                if config.was != "*" and initial_val != config.was:
                    continue

                # Condition: is_now
                if config.is_now != "*" and current_val != config.is_now:
                    continue
            # ------------------------------

            method = getattr(self, config.method_name)

            if config.on_commit:
                transaction.on_commit(method)
            else:
                method()

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding

        self._run_lifecycle_hooks(HookType.BEFORE_SAVE)
        if is_new:
            self._run_lifecycle_hooks(HookType.BEFORE_CREATE)
        else:
            self._run_lifecycle_hooks(HookType.BEFORE_UPDATE)

        super().save(*args, **kwargs)

        if is_new:
            self._run_lifecycle_hooks(HookType.AFTER_CREATE)
        else:
            self._run_lifecycle_hooks(HookType.AFTER_UPDATE)

        self._run_lifecycle_hooks(HookType.AFTER_SAVE)

        # Refresh snapshot only after a successful save
        self._take_lifecycle_snapshot()

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        self._run_lifecycle_hooks(HookType.BEFORE_DELETE)
        result = super().delete(*args, **kwargs)
        self._run_lifecycle_hooks(HookType.AFTER_DELETE)

        return result
