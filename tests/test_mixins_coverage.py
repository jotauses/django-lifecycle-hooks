import pytest
from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, WhenFieldValueIs, hook


class CoverageModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100, default="")
    status = models.CharField(max_length=20, default="new")

    # For nested test
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        app_label = "tests"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hooks_called = []

    @hook(HookType.BEFORE_DELETE)
    def before_delete(self) -> None:
        self.hooks_called.append("before_delete")

    @hook(HookType.AFTER_DELETE)
    def after_delete(self) -> None:
        self.hooks_called.append("after_delete")

    @hook(HookType.BEFORE_UPDATE)
    def before_update(self) -> None:
        self.hooks_called.append("before_update")

    @hook(HookType.AFTER_UPDATE)
    def after_update(self) -> None:
        self.hooks_called.append("after_update")

    @hook(HookType.AFTER_SAVE, when="name", has_changed=True)
    def name_changed(self) -> None:
        self.hooks_called.append("name_changed")

    @hook(HookType.AFTER_SAVE, when="status", was="new", is_now="done")
    def status_done(self) -> None:
        self.hooks_called.append("status_done")

    @hook(HookType.AFTER_SAVE, when="parent.name", is_now="parent")
    def parent_name_check(self) -> None:
        self.hooks_called.append("parent_name_check")

    @hook(HookType.AFTER_SAVE)
    async def async_hook(self) -> None:
        self.hooks_called.append("async_hook")

    @hook(HookType.AFTER_SAVE, condition=WhenFieldValueIs("name", "async_cond"))
    async def async_cond_hook(self) -> None:
        self.hooks_called.append("async_cond_hook")


@pytest.mark.django_db
def test_delete_hooks() -> None:
    instance = CoverageModel.objects.create(name="delete_me")
    instance.hooks_called = []

    instance.delete()

    assert "before_delete" in instance.hooks_called
    assert "after_delete" in instance.hooks_called


@pytest.mark.django_db
def test_has_changed_unwatched() -> None:
    instance = CoverageModel.objects.create(name="unwatched")
    # 'status' is watched by status_done hook, but we check a field that is NOT watched directly.
    # has_changed checks if it's in _lifecycle_initial_state.
    # If we check a field that is not in any hook's 'when', it won't be in snapshot.

    assert instance.has_changed("id") is False


@pytest.mark.django_db
def test_nested_field_none() -> None:
    # Test _get_value_from_path when intermediate is None
    instance = CoverageModel(name="child")
    instance.parent = None
    # This triggers snapshotting. 'parent.name' is watched.
    # _get_value_from_path("parent.name") should return None without error.

    instance.save()
    # No error should occur.


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_update_flow() -> None:
    instance = await CoverageModel.objects.acreate(name="async_test")
    instance.hooks_called = []

    instance.name = "updated"

    await instance.asave()

    assert "before_update" in instance.hooks_called
    assert "after_update" in instance.hooks_called
    assert "name_changed" in instance.hooks_called
    assert "async_hook" in instance.hooks_called


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_update_fields() -> None:
    instance = await CoverageModel.objects.acreate(name="async_fields")
    instance.hooks_called = []

    instance.name = "updated"
    # Update only 'status', so 'name' hooks should NOT run
    await instance.asave(update_fields=["status"])

    assert "name_changed" not in instance.hooks_called
    assert "async_hook" in instance.hooks_called


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_conditions() -> None:
    instance = await CoverageModel.objects.acreate(status="new")
    instance.hooks_called = []

    # Case 1: Condition Met
    instance.status = "done"
    await instance.asave()
    assert "status_done" in instance.hooks_called

    # Case 2: Condition NOT Met
    instance.hooks_called = []
    instance.status = "wip"  # Not "done"
    await instance.asave()
    assert "status_done" not in instance.hooks_called

    # Case 3: Async Condition Met
    instance.hooks_called = []
    instance.name = "async_cond"
    await instance.asave()
    assert "async_cond_hook" in instance.hooks_called

    # Case 4: Async Condition NOT Met
    instance.hooks_called = []
    instance.name = "other"
    await instance.asave()
    assert "async_cond_hook" not in instance.hooks_called


@pytest.mark.django_db
def test_sync_save_skips_async_hooks() -> None:
    instance = CoverageModel(name="sync_skip")
    instance.save()

    assert "async_hook" not in instance.hooks_called
