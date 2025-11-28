from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook
from django_lifecycle_hooks.checks import check_lifecycle_hooks


class BrokenModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_SAVE, when="non_existent_field")
    def broken_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, when="name.bad_attribute")
    def broken_fk_hook(self) -> None:
        pass


def test_system_checks() -> None:
    errors = check_lifecycle_hooks(app_configs=None)

    # Filter errors for BrokenModel
    broken_model_errors = [e for e in errors if e.obj == BrokenModel]

    assert len(broken_model_errors) >= 2

    ids = [e.id for e in broken_model_errors]
    assert "django_lifecycle_hooks.E001" in ids

    messages = [e.msg for e in broken_model_errors]
    assert any("watches non-existent field 'non_existent_field'" in m for m in messages)
    assert any("watches non-existent field 'name.bad_attribute'" in m for m in messages)
