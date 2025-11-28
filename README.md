# Django Lifecycle Hooks

**The high-performance, zero-overhead alternative to Django Signals.**

[![PyPI version](https://img.shields.io/pypi/v/django-lifecycle-hooks.svg?color=2c3e50&labelColor=ecf0f1)](https://pypi.org/project/django-lifecycle-hooks/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-lifecycle-hooks.svg?color=2c3e50&labelColor=ecf0f1)](https://pypi.org/project/django-lifecycle-hooks/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-lifecycle-hooks.svg?color=2c3e50&labelColor=ecf0f1)](https://pypi.org/project/django-lifecycle-hooks/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2c3e50.svg?labelColor=ecf0f1)](https://opensource.org/licenses/MIT)

---

## ⚡ Why this library?

**Stop slowing down your Django app with inefficient signals.**

Most lifecycle libraries (and Django's own signals) rely on heavy runtime introspection, full object copying, and loose coupling that makes debugging a nightmare.

**Django Lifecycle Hooks** is engineered for **performance-critical** applications:

- **🚀 Zero Runtime Overhead**: Hook resolution happens **once** at import time. Executing hooks is an **O(1)** operation.
- **💾 Sparse Snapshotting**: We don't copy your entire model. If you only watch `status`, we only cache `status`. Your memory usage stays flat.
- **🛡️ Type-Safe & Modern**: Built for **Python 3.14+** and **Django 5.2+**. Fully typed, `__slots__` optimized, and ready for strict MyPy validation.
- **✨ Developer Joy**: No more hunting for `@receiver` in random files. Logic lives where it belongs: **inside your model** or **specialized hooks**.

---

## 🏎️ Performance Comparison

| Feature | Standard Signals / Legacy Libs | Django Lifecycle Hooks |
| :--- | :--- | :--- |
| **Hook Resolution** | Runtime Introspection (Slow) | **Import-time Registry (Instant)** |
| **Change Detection** | Full `__dict__` copy (High RAM) | **Sparse Field Copy (Low RAM)** |
| **Lookup Speed** | O(n) Listener Loop | **O(1) Direct Dispatch** |
| **Async Support** | Limited / Hacky | **Native `asave` & `acreate` Support** |

---

## 🚀 Quick Start

### 1. Install
```bash
pip install django-lifecycle-hooks
```

### 2. Write Elegant Code
Inherit from `LifecycleModelMixin` and declare your logic.

```python
from django.db import models
from django_lifecycle_hooks import LifecycleModelMixin, hook, HookType

class UserAccount(LifecycleModelMixin, models.Model):
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="active")
    
    # ✅ 1. Simple & Fast
    @hook(HookType.BEFORE_SAVE)
    def clean_username(self):
        self.username = self.username.lower()

    # ✅ 2. Conditional & Declarative
    # Only runs when status changes to 'banned'. 
    # No "if" checks needed inside your method.
    @hook(HookType.AFTER_UPDATE, when="status", was="active", is_now="banned")
    def on_ban(self):
        self.ban_related_assets()

    # ✅ 3. Transaction Safe
    # Only fires after the DB transaction commits successfully.
    @hook(HookType.AFTER_SAVE, on_commit=True)
    def send_welcome_email(self):
        send_email_task.delay(self.id)
```

---

## 📚 Documentation

- [**User Guide**](docs/user-guide.md): Master advanced patterns (Async, Stacked Hooks, Conditions).
- [**API Reference**](docs/api.md): Detailed technical specs.

---
*Built for engineers who care about speed, clean code, and type safety ♥️*
