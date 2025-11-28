from django.db import models

from django_lifecycle_hooks.decorators import hook
from django_lifecycle_hooks.enums import HookType
from django_lifecycle_hooks.mixins import LifecycleModelMixin


class StackedHooksModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    count = models.IntegerField(default=0)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_CREATE)
    @hook(HookType.BEFORE_UPDATE)
    def increment_count(self) -> None:
        self.count += 1


def test_stacked_hooks(db) -> None:
    instance = StackedHooksModel(name="test")
    instance.save()

    assert instance.count == 1  # Triggered by BEFORE_CREATE

    instance.name = "updated"
    instance.save()

    assert instance.count == 2  # Triggered by BEFORE_UPDATE
