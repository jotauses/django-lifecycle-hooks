from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class Item(LifecycleModelMixin, models.Model):
    status = models.CharField(max_length=20, default="new")
    count = models.IntegerField(default=0)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hooks_called = []

    @hook(HookType.BEFORE_CREATE)
    def before_create_hook(self) -> None:
        self.hooks_called.append("before_create")

    @hook(HookType.AFTER_CREATE)
    def after_create_hook(self) -> None:
        self.hooks_called.append("after_create")

    @hook(HookType.BEFORE_UPDATE)
    def before_update_hook(self) -> None:
        self.hooks_called.append("before_update")

    @hook(HookType.AFTER_UPDATE)
    def after_update_hook(self) -> None:
        self.hooks_called.append("after_update")

    @hook(HookType.BEFORE_SAVE)
    def before_save_hook(self) -> None:
        self.hooks_called.append("before_save")

    @hook(HookType.AFTER_SAVE)
    def after_save_hook(self) -> None:
        self.hooks_called.append("after_save")

    @hook(HookType.BEFORE_UPDATE, when="status", was="new", is_now="done")
    def condition_hook(self) -> None:
        self.hooks_called.append("condition_met")

    @hook(HookType.AFTER_SAVE, when="count", has_changed=True)
    def change_hook(self) -> None:
        self.hooks_called.append("count_changed")
