from typing import Any, List

from django.core.checks import Error, Tags, register
from django.db import models

from .core import LifecycleRegistry


def _check_model_hooks(model: type[models.Model]) -> List[Error]:
    errors = []
    registry: LifecycleRegistry = getattr(model, "_lifecycle_registry", None)

    if not registry:
        return errors

    # Check watched fields
    for trigger, hooks in registry._hooks.items():
        for hook_config in hooks:
            # Check 'when' field
            if hook_config.when:
                if not _field_exists(model, hook_config.when):
                    errors.append(
                        Error(
                            (
                                f"Hook '{hook_config.method_name}' watches non-existent field "
                                f"'{hook_config.when}'."
                            ),
                            obj=model,
                            id="django_lifecycle_hooks.E001",
                        )
                    )

            # Check fields in condition
            if hook_config.condition:
                condition_fields = registry._extract_fields_from_condition(
                    hook_config.condition
                )
                for field_name in condition_fields:
                    if not _field_exists(model, field_name):
                        errors.append(
                            Error(
                                (
                                    f"Hook '{hook_config.method_name}' condition references "
                                    f"non-existent field '{field_name}'."
                                ),
                                obj=model,
                                id="django_lifecycle_hooks.E002",
                            )
                        )

    return errors


def _field_exists(model: type[models.Model], field_path: str) -> bool:
    """
    Checks if a field exists on the model, supporting dot notation for related fields.
    """
    parts = field_path.split(".")
    current_model = model

    for i, part in enumerate(parts):
        try:
            field = current_model._meta.get_field(part)
        except Exception:
            # Field not found.
            # It might be a property or method, which we can't easily validate statically.
            # Since the library supports watching any attribute, we allow this but cannot
            # strictly enforce it as a DB field.
            # Let's check if it's a property or attribute on the class.
            if hasattr(current_model, part):
                # It exists as an attribute (e.g. property, method)
                # If it's the last part, it's valid.
                # If it's not the last part, we can't easily know the type of the property to continue traversing.
                if i == len(parts) - 1:
                    return True
                else:
                    # Can't validate further for properties
                    return True
            return False

        if i < len(parts) - 1:
            # Need to traverse to related model
            if field.is_relation and field.related_model:
                current_model = field.related_model
            else:
                # Not a relation, but we have more parts. Invalid path.
                return False

    return True


@register(Tags.models)
def check_lifecycle_hooks(app_configs: Any = None, **kwargs: Any) -> List[Error]:
    from django.apps import apps

    errors = []
    if app_configs is None:
        app_configs = apps.get_app_configs()

    for app_config in app_configs:
        for model in app_config.get_models():
            if hasattr(model, "_lifecycle_registry"):
                errors.extend(_check_model_hooks(model))

    return errors
