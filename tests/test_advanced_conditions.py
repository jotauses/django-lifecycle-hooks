from django.db import models

from django_lifecycle_hooks import (
    HookType,
    LifecycleModelMixin,
    WhenFieldHasChanged,
    WhenFieldValueIs,
    hook,
)


class AdvancedConditionsModel(LifecycleModelMixin, models.Model):
    status = models.CharField(max_length=20, default="new")
    category = models.CharField(max_length=20, default="A")
    flag = models.BooleanField(default=False)

    class Meta:
        app_label = "tests"

    @hook(
        HookType.BEFORE_UPDATE,
        condition=WhenFieldHasChanged("status") & WhenFieldValueIs("category", "B"),
    )
    def on_status_change_and_category_b(self) -> None:
        self.flag = True


def test_advanced_conditions(db) -> None:
    instance = AdvancedConditionsModel(status="new", category="A")
    instance.save()

    # Change status but category is A -> Should NOT trigger
    instance.status = "active"
    instance.save()
    assert instance.flag is False

    # Change category to B but status not changed -> Should NOT trigger
    instance.category = "B"
    instance.save()
    assert instance.flag is False

    # Change status AND category is B -> Should TRIGGER
    instance.status = "completed"
    instance.save()
    assert instance.flag is True
