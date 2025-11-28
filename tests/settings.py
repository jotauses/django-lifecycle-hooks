DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
INSTALLED_APPS = [
    "tests",
    "django_lifecycle_hooks",
]
SECRET_KEY = "test-key"
