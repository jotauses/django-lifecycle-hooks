from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class SkipHooksModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    hook_ran = models.BooleanField(default=False)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_SAVE)
    def on_save(self) -> None:
        self.hook_ran = True


def test_skip_hooks(db) -> None:
    instance = SkipHooksModel(name="test")
    instance.save(skip_hooks=True)

    assert instance.hook_ran is False

    instance.save()
    assert instance.hook_ran is True
