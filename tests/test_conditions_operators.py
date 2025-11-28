from unittest.mock import Mock

from django.db import models

from django_lifecycle_hooks import (
    AndCondition,
    LifecycleModelMixin,
    NotCondition,
    OrCondition,
    WhenFieldHasChanged,
    WhenFieldValueChangesTo,
    WhenFieldValueIs,
    WhenFieldValueIsNot,
    WhenFieldValueWas,
    WhenFieldValueWasNot,
)


class OperatorModel(LifecycleModelMixin, models.Model):
    status = models.CharField(max_length=20, default="new")
    count = models.IntegerField(default=0)

    class Meta:
        app_label = "tests"


def test_condition_operators() -> None:
    instance = OperatorModel()

    # Basic conditions
    c1 = WhenFieldValueIs("status", "done")
    c2 = WhenFieldValueIs("count", 5)

    # AND
    and_cond = c1 & c2
    assert isinstance(and_cond, AndCondition)
    assert and_cond.c1 == c1
    assert and_cond.c2 == c2

    # OR
    or_cond = c1 | c2
    assert isinstance(or_cond, OrCondition)
    assert or_cond.c1 == c1
    assert or_cond.c2 == c2

    # NOT
    not_cond = ~c1
    assert isinstance(not_cond, NotCondition)
    assert not_cond.c == c1


def test_chained_operators() -> None:
    c1 = WhenFieldValueIs("status", "done")
    c2 = WhenFieldValueIs("count", 5)
    c3 = WhenFieldHasChanged("status")

    # (c1 & c2) | c3
    chain1 = (c1 & c2) | c3
    assert isinstance(chain1, OrCondition)
    assert isinstance(chain1.c1, AndCondition)
    assert chain1.c2 == c3

    # c1 & (c2 | c3)
    chain2 = c1 & (c2 | c3)
    assert isinstance(chain2, AndCondition)
    assert chain2.c1 == c1
    assert isinstance(chain2.c2, OrCondition)

    # ~(c1 & c2)
    chain3 = ~(c1 & c2)
    assert isinstance(chain3, NotCondition)
    assert isinstance(chain3.c, AndCondition)


def test_all_condition_classes_operators_and_checks() -> None:
    # Instantiate one of each to test their specific __and__, __or__, __invert__
    conditions = [
        WhenFieldHasChanged("status"),
        WhenFieldValueIs("status", "done"),
        WhenFieldValueIsNot("status", "new"),
        WhenFieldValueWas("status", "draft"),
        WhenFieldValueWasNot("status", "deleted"),
        WhenFieldValueChangesTo("status", "published"),
        AndCondition(WhenFieldHasChanged("a"), WhenFieldHasChanged("b")),
        OrCondition(WhenFieldHasChanged("a"), WhenFieldHasChanged("b")),
        NotCondition(WhenFieldHasChanged("a")),
    ]

    base = WhenFieldValueIs("other", "val")

    # Mock instance for check() verification
    instance = Mock()
    instance.has_changed.return_value = True
    instance.current_value.return_value = "val"
    instance.initial_value.return_value = "old"

    for c in conditions:
        # Test &
        res_and = c & base
        assert isinstance(res_and, AndCondition)
        assert res_and.c1 == c
        assert res_and.c2 == base
        # Verify check() calls both
        res_and.check(instance)

        # Test |
        res_or = c | base
        assert isinstance(res_or, OrCondition)
        assert res_or.c1 == c
        assert res_or.c2 == base
        # Verify check() calls
        res_or.check(instance)

        # Test ~
        res_not = ~c
        if isinstance(c, NotCondition):
            # Double negation optimization: ~~A -> A
            assert res_not == c.c
        else:
            assert isinstance(res_not, NotCondition)
            assert res_not.c == c
            # Verify check()
            res_not.check(instance)

        # Verify check() on the condition itself
        c.check(instance)


def test_specific_checks() -> None:
    instance = Mock()

    # WhenFieldHasChanged
    instance.has_changed.return_value = True
    assert WhenFieldHasChanged("f").check(instance) is True
    instance.has_changed.return_value = False
    assert WhenFieldHasChanged("f").check(instance) is False

    # WhenFieldValueIs
    instance.current_value.return_value = "A"
    assert WhenFieldValueIs("f", "A").check(instance) is True
    assert WhenFieldValueIs("f", "B").check(instance) is False

    # WhenFieldValueIsNot
    instance.current_value.return_value = "A"
    assert WhenFieldValueIsNot("f", "B").check(instance) is True
    assert WhenFieldValueIsNot("f", "A").check(instance) is False

    # WhenFieldValueWas
    instance.initial_value.return_value = "A"
    assert WhenFieldValueWas("f", "A").check(instance) is True
    assert WhenFieldValueWas("f", "B").check(instance) is False

    # WhenFieldValueWasNot
    instance.initial_value.return_value = "A"
    assert WhenFieldValueWasNot("f", "B").check(instance) is True
    assert WhenFieldValueWasNot("f", "A").check(instance) is False

    # WhenFieldValueChangesTo
    instance.has_changed.return_value = True
    instance.current_value.return_value = "A"
    assert WhenFieldValueChangesTo("f", "A").check(instance) is True

    instance.has_changed.return_value = False
    assert WhenFieldValueChangesTo("f", "A").check(instance) is False

    instance.has_changed.return_value = True
    instance.current_value.return_value = "B"
    assert WhenFieldValueChangesTo("f", "A").check(instance) is False
