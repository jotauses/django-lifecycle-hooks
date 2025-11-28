from io import StringIO

from django.core.management import call_command
from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class IntrospectionModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_SAVE, when="name", priority=5)
    def my_hook(self) -> None:
        pass

    @hook(HookType.AFTER_SAVE)
    async def my_async_hook(self) -> None:
        pass


def test_list_hooks_command() -> None:
    out = StringIO()
    call_command("list_hooks", stdout=out)

    output = out.getvalue()

    assert "Model: tests.IntrospectionModel" in output
    assert "my_hook" in output
    assert "before_save" in output
    assert "name" in output
    assert "5" in output  # Priority

    assert "my_async_hook" in output
    assert "after_save" in output
    assert "Yes" in output  # Async
