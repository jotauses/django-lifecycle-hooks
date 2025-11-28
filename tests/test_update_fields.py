from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class UpdateFieldsModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="new")
    name_hook_ran = models.BooleanField(default=False)
    status_hook_ran = models.BooleanField(default=False)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_UPDATE, when="name", has_changed=True)
    def on_name_change(self) -> None:
        self.name_hook_ran = True

    @hook(HookType.BEFORE_UPDATE, when="status", has_changed=True)
    def on_status_change(self) -> None:
        self.status_hook_ran = True


def test_update_fields(db) -> None:
    instance = UpdateFieldsModel(name="initial", status="new")
    instance.save()

    # Reset flags
    instance.name_hook_ran = False
    instance.status_hook_ran = False

    # Update only name
    instance.name = "changed"
    instance.status = "changed"  # Changed in memory but not in update_fields

    instance.save(update_fields=["name"])

    assert instance.name_hook_ran is True
    assert (
        instance.status_hook_ran is False
    )  # Should be skipped because 'status' is not in update_fields
