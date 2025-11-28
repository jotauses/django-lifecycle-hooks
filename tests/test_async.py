import pytest
from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class AsyncModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    sync_hook_ran = models.BooleanField(default=False)
    async_hook_ran = models.BooleanField(default=False)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_SAVE)
    def sync_hook(self) -> None:
        self.sync_hook_ran = True

    @hook(HookType.AFTER_SAVE)
    async def async_hook(self) -> None:
        self.async_hook_ran = True


@pytest.mark.asyncio
async def test_async_save(db) -> None:
    instance = AsyncModel(name="test")

    # Verify hooks haven't run
    assert instance.sync_hook_ran is False
    assert instance.async_hook_ran is False

    # Run async save
    await instance.asave()

    # Verify both hooks ran
    # Sync hook should be wrapped and run
    # Async hook should be awaited directly
    assert instance.sync_hook_ran is True
    assert instance.async_hook_ran is True


@pytest.mark.asyncio
async def test_async_save_skip_hooks(db) -> None:
    instance = AsyncModel(name="test_skip")

    await instance.asave(skip_hooks=True)

    assert instance.sync_hook_ran is False
    assert instance.async_hook_ran is False
