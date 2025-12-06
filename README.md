# 🪝 Django Lifecycle Hooks

> **High-performance, declarative lifecycle hooks for your Django models.**

[![Documentation](https://img.shields.io/badge/docs-live-brightgreen)](https://jotauses.github.io/django-lifecycle-hooks/)
[![Tests](https://img.shields.io/badge/tests-passing-success)](https://github.com/jotauses/django-lifecycle-hooks)
[![Coverage](https://img.shields.io/badge/coverage-100%25-success)](https://github.com/jotauses/django-lifecycle-hooks)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-4.2%20|%205.0%20|%205.1%20|%205.2-green)](https://www.djangoproject.com/)

**Full Documentation**: [https://jotauses.github.io/django-lifecycle-hooks/](https://jotauses.github.io/django-lifecycle-hooks/)

## 📋 Requirements

*   **Python**: 3.10, 3.11, 3.12, 3.13, 3.14
*   **Django**: 4.2 (LTS), 5.0, 5.1, 5.2

---

## 🌟 Why Django Lifecycle Hooks?

Stop slowing down your Django app with inefficient signals. You need a solution that is:

*   **Zero Runtime Overhead:** Hook resolution happens **once** at import time. O(1) dispatch.
*   **Ultra Efficient:** Sparse snapshotting—we only cache what you watch.
*   **Async Native:** The **only** library with first-class `asave` and `acreate` support.
*   **Developer Friendly:** Type-safe, declarative API that lives inside your model.

## 🚀 Quick Start

### 1. Installation

```bash
pip install django-lifecycle-hooks
```

### 2. Add to your App

Add `django_lifecycle_hooks` to your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_lifecycle_hooks',
    ...
]
```

### 3. Enable Hooks

Inherit from `LifecycleModelMixin` in your model. That's it!

```python
from django.db import models
from django_lifecycle_hooks import LifecycleModelMixin, hook, HookType

class UserAccount(LifecycleModelMixin, models.Model):
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="active")

    @hook(HookType.BEFORE_SAVE)
    def clean_username(self):
        self.username = self.username.lower()
```

---

## 📖 Usage Guide

### Simple Hooks

Replace messy signals with clean, decorated methods.

```python
@hook(HookType.AFTER_CREATE)
def on_create(self):
    print(f"User {self.username} created!")
```

### 🔀 Conditional Execution

Only run logic when specific fields change. No more `if` spaghetti.

```python
# Only runs when status changes from 'active' to 'banned'
@hook(HookType.AFTER_UPDATE, when="status", was="active", is_now="banned")
def on_ban(self):
    self.ban_related_assets()
```

### ⚡ Async & ASGI Support

We don't just wrap sync code; we await your async hooks properly.

```python
@hook(HookType.AFTER_SAVE)
async def send_welcome_email(self):
    await email_service.send_async(self.email)
```

### 🛡️ Transaction Safety

Ensure your hooks only fire after the database transaction commits.

```python
@hook(HookType.AFTER_SAVE, on_commit=True)
def trigger_background_job(self):
    # This task is only queued if the transaction succeeds
    process_data.delay(self.id)
```

### 🏎️ Performance Comparison

| Feature | Standard Signals | Django Lifecycle Hooks |
| :--- | :--- | :--- |
| **Hook Resolution** | Runtime Introspection (Slow) | **Import-time Registry (Instant)** |
| **Change Detection** | Full `__dict__` copy (High RAM) | **Sparse Field Copy (Low RAM)** |
| **Lookup Speed** | O(n) Listener Loop | **O(1) Direct Dispatch** |
| **Async / ASGI** | ❌ None or Hacky Wrappers | **✅ Native `asave` & `acreate` Support** |

---

## 🧪 Running Tests

We use `pytest` for a robust testing suite.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=django_lifecycle_hooks
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

*Built for engineers who care about speed, clean code and type safety ❤️ by Joaquín Vázquez*
