from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand

from django_lifecycle_hooks.core import LifecycleRegistry


class Command(BaseCommand):
    help = "List all registered lifecycle hooks for models."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Django Lifecycle Hooks Registry"))
        
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if hasattr(model, "_lifecycle_registry"):
                    self._print_model_hooks(model)

    def _print_model_hooks(self, model: Any) -> None:
        registry: LifecycleRegistry = model._lifecycle_registry
        if not registry._hooks:
            return

        self.stdout.write(f"\nModel: {self.style.SUCCESS(model._meta.label)}")
        
        # Header
        headers = ["Method", "Trigger", "When", "Condition", "Priority", "Async"]
        row_format = "{:<30} {:<20} {:<20} {:<20} {:<10} {:<5}"
        self.stdout.write(row_format.format(*headers))
        self.stdout.write("-" * 110)

        for trigger, hooks in registry._hooks.items():
            for config in hooks:
                condition_str = str(config.condition) if config.condition else "-"
                # Truncate long conditions
                if len(condition_str) > 20:
                    condition_str = condition_str[:17] + "..."
                
                when_str = config.when or "-"
                
                self.stdout.write(
                    row_format.format(
                        config.method_name,
                        trigger,
                        when_str,
                        condition_str,
                        str(config.priority),
                        "Yes" if config.is_async else "No",
                    )
                )
