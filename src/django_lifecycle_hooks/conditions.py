from typing import Any, Protocol


class Condition(Protocol):
    """
    Protocol defining the interface for a lifecycle condition.
    """

    def check(self, instance: Any) -> bool:
        """Evaluate the condition against the model instance."""
        ...

    def __and__(self, other: "Condition") -> "Condition": ...

    def __or__(self, other: "Condition") -> "Condition": ...

    def __invert__(self) -> "Condition": ...


class BaseCondition:
    """Base class for conditions implementing logical operators."""

    def __and__(self, other: "Condition") -> "Condition":
        return AndCondition(self, other)

    def __or__(self, other: "Condition") -> "Condition":
        return OrCondition(self, other)

    def __invert__(self) -> "Condition":
        return NotCondition(self)  # type: ignore


class AndCondition(BaseCondition):
    """Combines two conditions with logical AND."""

    __slots__ = ("c1", "c2")

    def __init__(self, c1: Condition, c2: Condition):
        self.c1 = c1
        self.c2 = c2

    def check(self, instance: Any) -> bool:
        return self.c1.check(instance) and self.c2.check(instance)


class OrCondition(BaseCondition):
    """Combines two conditions with logical OR."""

    __slots__ = ("c1", "c2")

    def __init__(self, c1: Condition, c2: Condition):
        self.c1 = c1
        self.c2 = c2

    def check(self, instance: Any) -> bool:
        return self.c1.check(instance) or self.c2.check(instance)


class NotCondition(BaseCondition):
    """Negates a condition."""

    __slots__ = ("c",)

    def __init__(self, c: Condition):
        self.c = c

    def check(self, instance: Any) -> bool:
        return not self.c.check(instance)

    def __invert__(self) -> Condition:
        # Double negation optimization: ~~A -> A
        return self.c


class WhenFieldHasChanged(BaseCondition):
    """Condition that checks if a field has changed."""

    __slots__ = ("field_name",)

    def __init__(self, field_name: str):
        self.field_name = field_name

    def check(self, instance: Any) -> bool:
        return instance.has_changed(self.field_name)


class WhenFieldValueIs(BaseCondition):
    """Condition that checks if a field's current value matches a value."""

    __slots__ = ("field_name", "value")

    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value

    def check(self, instance: Any) -> bool:
        return instance.current_value(self.field_name) == self.value


class WhenFieldValueIsNot(BaseCondition):
    """Condition that checks if a field's current value does not match a value."""

    __slots__ = ("field_name", "value")

    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value

    def check(self, instance: Any) -> bool:
        return instance.current_value(self.field_name) != self.value


class WhenFieldValueWas(BaseCondition):
    """Condition that checks if a field's initial value matches a value."""

    __slots__ = ("field_name", "value")

    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value

    def check(self, instance: Any) -> bool:
        return instance.initial_value(self.field_name) == self.value


class WhenFieldValueWasNot(BaseCondition):
    """Condition that checks if a field's initial value does not match a value."""

    __slots__ = ("field_name", "value")

    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value

    def check(self, instance: Any) -> bool:
        return instance.initial_value(self.field_name) != self.value


class WhenFieldValueChangesTo(BaseCondition):
    """Condition that checks if a field has changed AND its new value matches a value."""

    __slots__ = ("field_name", "value")

    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value

    def check(self, instance: Any) -> bool:
        return (
            instance.has_changed(self.field_name)
            and instance.current_value(self.field_name) == self.value
        )
