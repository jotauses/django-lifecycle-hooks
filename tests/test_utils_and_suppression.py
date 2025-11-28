from django.db import models

from django_lifecycle_hooks.decorators import hook
from django_lifecycle_hooks.enums import HookType
from django_lifecycle_hooks.mixins import LifecycleModelMixin


class UtilsModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="new")

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_UPDATE, when="name", has_changed=True)
    def on_name_change(self) -> None:
        # Test has_changed inside hook
        if self.has_changed("name"):
            self.status = "name_changed"


def test_utils_and_suppression(db) -> None:
    instance = UtilsModel(name="initial")
    instance.save()

    # Test initial_value and current_value
    assert instance.initial_value("name") == "initial"
    assert instance.current_value("name") == "initial"

    instance.name = "changed"
    assert instance.has_changed("name") is True
    assert instance.initial_value("name") == "initial"
    assert instance.current_value("name") == "changed"

    instance.save()
    assert instance.status == "name_changed"

    # Test suppression
    instance.status = "reset"
    instance.save()

    with instance.suppress_hooked_methods():
        instance.name = "changed_again"
        instance.save()

    # Hook should NOT have run
    assert instance.status == "reset"

    # Verify it works again after suppression
    instance.name = "changed_back"
    instance.save()
    assert instance.status == "name_changed"
