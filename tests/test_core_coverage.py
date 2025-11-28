from django.db import models

from django_lifecycle_hooks import (
    AndCondition,
    NotCondition,
    OrCondition,
    WhenFieldHasChanged,
    WhenFieldValueIs,
)
from django_lifecycle_hooks.core import LifecycleRegistry


class CoreModel(models.Model):
    class Meta:
        app_label = "tests"


def test_extract_fields_from_condition() -> None:
    registry = LifecycleRegistry(CoreModel)

    # Simple condition
    c1 = WhenFieldHasChanged("field1")
    fields = registry._extract_fields_from_condition(c1)
    assert fields == {"field1"}

    # AndCondition
    c2 = AndCondition(WhenFieldHasChanged("field2"), WhenFieldValueIs("field3", "val"))
    fields = registry._extract_fields_from_condition(c2)
    assert fields == {"field2", "field3"}

    # OrCondition
    c3 = OrCondition(WhenFieldHasChanged("field4"), WhenFieldHasChanged("field5"))
    fields = registry._extract_fields_from_condition(c3)
    assert fields == {"field4", "field5"}

    # NotCondition
    c4 = NotCondition(WhenFieldHasChanged("field6"))
    fields = registry._extract_fields_from_condition(c4)
    assert fields == {"field6"}

    # Nested complex
    # (field7 & field8) | ~field9
    c5 = OrCondition(
        AndCondition(WhenFieldHasChanged("field7"), WhenFieldHasChanged("field8")),
        NotCondition(WhenFieldHasChanged("field9")),
    )
    fields = registry._extract_fields_from_condition(c5)
    assert fields == {"field7", "field8", "field9"}


def test_registry_properties() -> None:
    registry = LifecycleRegistry(CoreModel)
    assert registry.watched_fields == set()
    assert registry.get_hooks("some_trigger") == []
