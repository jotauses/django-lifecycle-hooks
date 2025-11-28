from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class PriorityModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    execution_order = []

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_SAVE, priority=10)
    def high_priority(self) -> None:
        self.execution_order.append("high")

    @hook(HookType.BEFORE_SAVE, priority=0)
    def default_priority(self) -> None:
        self.execution_order.append("default")

    @hook(HookType.BEFORE_SAVE, priority=20)
    def highest_priority(self) -> None:
        self.execution_order.append("highest")


def test_priority(db) -> None:
    instance = PriorityModel(name="test")
    instance.execution_order = []  # Reset for instance
    instance.save()

    # Expected order: highest (20), high (10), default (0)
    assert instance.execution_order == ["highest", "high", "default"]
