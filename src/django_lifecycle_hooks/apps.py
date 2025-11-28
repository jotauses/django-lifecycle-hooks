from django.apps import AppConfig


class DjangoLifecycleHooksConfig(AppConfig):
    name = "django_lifecycle_hooks"
    verbose_name = "Django Lifecycle Hooks"

    def ready(self) -> None:
        pass
