from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, WhenFieldValueIs, hook
from django_lifecycle_hooks.checks import (
    _check_model_hooks,
    _field_exists,
    check_lifecycle_hooks,
)


class ChecksModel(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)

    @property
    def my_prop(self):
        return "prop"

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_SAVE, when="name")
    def valid_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, when="parent.name")
    def valid_nested_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, when="my_prop")
    def valid_prop_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, when="invalid_field")
    def invalid_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, when="parent.invalid_field")
    def invalid_nested_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, when="name.invalid_traversal")
    def invalid_traversal_hook(self) -> None:
        pass

    @hook(HookType.BEFORE_SAVE, condition=WhenFieldValueIs("invalid_cond_field", "val"))
    def invalid_condition_hook(self) -> None:
        pass


def test_field_exists_logic() -> None:
    # Direct field
    assert _field_exists(ChecksModel, "name") is True
    assert _field_exists(ChecksModel, "invalid") is False

    # Nested field
    assert _field_exists(ChecksModel, "parent.name") is True
    assert _field_exists(ChecksModel, "parent.invalid") is False

    # Invalid traversal (name is not a relation)
    assert _field_exists(ChecksModel, "name.something") is False

    # Property
    assert _field_exists(ChecksModel, "my_prop") is True
    assert _field_exists(ChecksModel, "invalid_prop") is False

    # Property traversal (can't validate deep)
    assert _field_exists(ChecksModel, "my_prop.something") is True


def test_check_model_hooks_errors() -> None:
    errors = _check_model_hooks(ChecksModel)
    error_ids = [e.id for e in errors]
    error_msgs = [e.msg for e in errors]

    # Should catch:
    # 1. invalid_field (E001)
    # 2. parent.invalid_field (E001)
    # 3. name.invalid_traversal (E001)
    # 4. invalid_cond_field (E002)

    assert "django_lifecycle_hooks.E001" in error_ids
    assert "django_lifecycle_hooks.E002" in error_ids

    assert any("watches non-existent field 'invalid_field'" in m for m in error_msgs)
    assert any(
        "watches non-existent field 'parent.invalid_field'" in m for m in error_msgs
    )
    assert any(
        "watches non-existent field 'name.invalid_traversal'" in m for m in error_msgs
    )
    assert any(
        "references non-existent field 'invalid_cond_field'" in m for m in error_msgs
    )


def test_check_model_hooks_no_registry() -> None:
    class NoRegistryModel(models.Model):
        class Meta:
            app_label = "tests"

    errors = _check_model_hooks(NoRegistryModel)
    assert errors == []


def test_check_lifecycle_hooks_integration() -> None:
    # Test the main check function
    # We pass None to check all apps, or specific app config

    # Mock app configs to avoid checking everything in the project
    # But we want to verify it finds our ChecksModel errors

    # Let's just call it with default args, it should run without error
    # and return a list of errors (including ours from ChecksModel)
    errors = check_lifecycle_hooks(app_configs=None)
    assert isinstance(errors, list)

    # Verify it found errors from ChecksModel
    found_ours = False
    for e in errors:
        if e.obj == ChecksModel:
            found_ours = True
            break
    assert found_ours is True
