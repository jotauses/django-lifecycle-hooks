from contextlib import contextmanager
from typing import Any, ClassVar, Generator, override

from django.db import transaction

from .core import LifecycleRegistry
from .enums import HookType


class LifecycleModelMixin:
    """
    High-performance Mixin to add lifecycle hooks capabilities.

    Architecture:
    - Uses __init_subclass__ to build the registry at startup.
    - Uses sparse snapshotting (only copies watched fields).
    - Inlines condition checks for maximum CPU efficiency.
    """

    _lifecycle_registry: ClassVar[LifecycleRegistry]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Initialize registry once at class creation (Startup)
        cls._lifecycle_registry = LifecycleRegistry(cls)

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._lifecycle_initial_state: dict[str, Any] = {}
        self._lifecycle_hooks_suppressed = False
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

        for field_path in registry.watched_fields:
            self._lifecycle_initial_state[field_path] = self._get_value_from_path(
                field_path
            )

    def _get_value_from_path(self, path: str) -> Any:
        """
        Traverses dot notation to get value.
        """
        value = self
        for part in path.split("."):
            if value is None:
                return None
            value = getattr(value, part, None)
        return value

    def _run_lifecycle_hooks(
        self, trigger: HookType, update_fields: Any = None
    ) -> None:
        """
        Executes hooks for the given trigger.
        Logic is inlined to avoid function call overhead in tight loops.
        """
        registry = self.__class__._lifecycle_registry  # type: ignore
        hooks = registry.get_hooks(trigger)

        if not hooks or self._lifecycle_hooks_suppressed:
            return

        initial_state = self._lifecycle_initial_state

        for config in hooks:
            # Optimization: If update_fields is present, skip hooks not watching those fields
            if update_fields and config.when and config.when not in update_fields:
                continue
            # --- Inline Condition Check ---
            if config.when:
                current_val = self._get_value_from_path(config.when)
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

            # Condition: condition (Advanced)
            if config.condition and not config.condition.check(self):
                continue
            # ------------------------------

            # Skip async hooks in synchronous execution
            if config.is_async:
                continue

            method = getattr(self, config.method_name)

            if config.on_commit:
                transaction.on_commit(method)
            else:
                method()

    @override
    def save(self, *args: Any, skip_hooks: bool = False, **kwargs: Any) -> None:
        if skip_hooks:
            super().save(*args, **kwargs)
            return

        is_new = self._state.adding
        update_fields = kwargs.get("update_fields")

        self._run_lifecycle_hooks(HookType.BEFORE_SAVE, update_fields=update_fields)
        if is_new:
            self._run_lifecycle_hooks(
                HookType.BEFORE_CREATE, update_fields=update_fields
            )
        else:
            self._run_lifecycle_hooks(
                HookType.BEFORE_UPDATE, update_fields=update_fields
            )

        super().save(*args, **kwargs)

        if is_new:
            self._run_lifecycle_hooks(
                HookType.AFTER_CREATE, update_fields=update_fields
            )
        else:
            self._run_lifecycle_hooks(
                HookType.AFTER_UPDATE, update_fields=update_fields
            )

        self._run_lifecycle_hooks(HookType.AFTER_SAVE, update_fields=update_fields)

        # Refresh snapshot only after a successful save
        self._take_lifecycle_snapshot()

    @override
    async def asave(self, *args: Any, skip_hooks: bool = False, **kwargs: Any) -> None:
        """
        Asynchronous version of save() with full lifecycle hook support.
        """
        if skip_hooks:
            with self.suppress_hooked_methods():
                await super().asave(*args, **kwargs)
            return

        is_new = self._state.adding
        update_fields = kwargs.get("update_fields")

        # Preserve initial state for AFTER_SAVE hooks because super().asave() -> save()
        # will update the snapshot prematurely.
        preserved_state = self._lifecycle_initial_state.copy()

        await self._run_lifecycle_hooks_async(
            HookType.BEFORE_SAVE, update_fields=update_fields
        )
        if is_new:
            await self._run_lifecycle_hooks_async(
                HookType.BEFORE_CREATE, update_fields=update_fields
            )
        else:
            await self._run_lifecycle_hooks_async(
                HookType.BEFORE_UPDATE, update_fields=update_fields
            )

        # Suppress hooks in the underlying save() call to avoid double execution
        # since super().asave() calls self.save()
        with self.suppress_hooked_methods():
            await super().asave(*args, **kwargs)

        if is_new:
            await self._run_lifecycle_hooks_async(
                HookType.AFTER_CREATE,
                update_fields=update_fields,
                initial_state_override=preserved_state,
            )
        else:
            await self._run_lifecycle_hooks_async(
                HookType.AFTER_UPDATE,
                update_fields=update_fields,
                initial_state_override=preserved_state,
            )

        await self._run_lifecycle_hooks_async(
            HookType.AFTER_SAVE,
            update_fields=update_fields,
            initial_state_override=preserved_state,
        )

        # Refresh snapshot only after a successful save
        self._take_lifecycle_snapshot()

    async def _run_lifecycle_hooks_async(
        self,
        trigger: HookType,
        update_fields: Any = None,
        initial_state_override: dict[str, Any] | None = None,
    ) -> None:
        """
        Executes hooks asynchronously.
        Wraps synchronous hooks in sync_to_async.
        """
        registry = self.__class__._lifecycle_registry  # type: ignore
        hooks = registry.get_hooks(trigger)

        if not hooks or self._lifecycle_hooks_suppressed:
            return

        initial_state = (
            initial_state_override
            if initial_state_override is not None
            else self._lifecycle_initial_state
        )

        # Import here to avoid circular imports or unnecessary overhead in sync path
        from asgiref.sync import sync_to_async

        for config in hooks:
            # Optimization: If update_fields is present, skip hooks not watching those fields
            if update_fields and config.when and config.when not in update_fields:
                continue

            # --- Inline Condition Check (Sync logic is fine here as it's just dict lookup) ---
            if config.when:
                current_val = self._get_value_from_path(config.when)
                initial_val = initial_state.get(config.when)

                if config.has_changed and current_val == initial_val:
                    continue
                if config.was != "*" and initial_val != config.was:
                    continue
                if config.is_now != "*" and current_val != config.is_now:
                    continue

            if config.condition and not config.condition.check(self):
                continue
            # ------------------------------

            method = getattr(self, config.method_name)

            if config.is_async:
                await method()
            else:
                # Wrap sync hook in sync_to_async
                await sync_to_async(method)()

    @override
    def delete(self, *args: Any, **kwargs: Any) -> Any:
        self._run_lifecycle_hooks(HookType.BEFORE_DELETE)
        result = super().delete(*args, **kwargs)
        self._run_lifecycle_hooks(HookType.AFTER_DELETE)

        return result

    def has_changed(self, field_name: str) -> bool:
        """
        Checks if the field has changed since the last save/init.
        """
        if field_name not in self._lifecycle_initial_state:
            # Performance Optimization: We only snapshot fields that are explicitly watched.
            # If a field is not watched, we cannot reliably determine if it has changed
            # without incurring the overhead of snapshotting the entire model.
            return False

        return self.current_value(field_name) != self.initial_value(field_name)

    def initial_value(self, field_name: str) -> Any:
        """
        Returns the initial value of the field when the instance was loaded.
        """
        return self._lifecycle_initial_state.get(field_name)

    def current_value(self, field_name: str) -> Any:
        """
        Returns the current value of the field.
        """
        return self._get_value_from_path(field_name)

    @contextmanager
    def suppress_hooked_methods(self) -> Generator[None, None, None]:
        """
        Context manager to temporarily suppress all lifecycle hooks.
        """
        original_state = self._lifecycle_hooks_suppressed
        self._lifecycle_hooks_suppressed = True
        try:
            yield
        finally:
            self._lifecycle_hooks_suppressed = original_state
