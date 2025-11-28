# Django Lifecycle Hooks

[![PyPI version](https://img.shields.io/pypi/v/django-lifecycle-hooks.svg?color=blue)](https://pypi.org/project/django-lifecycle-hooks/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-lifecycle-hooks.svg?color=blue)](https://pypi.org/project/django-lifecycle-hooks/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-lifecycle-hooks.svg?color=blue)](https://pypi.org/project/django-lifecycle-hooks/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The next-generation, high-performance declarative lifecycle hooks library for Django.**

Engineered for **Enterprise** projects requiring surgical precision, zero runtime overhead, and full compatibility with the modern Python stack (3.10 through 3.14+) and Django 4.x+.

---

## 🚀 Why this library?

Legacy lifecycle libraries rely on heavy runtime introspection and full object copying, causing significant memory bloat and CPU drag. **Django Lifecycle Hooks** changes the game:

* **⚡ Zero-Overhead Runtime:** The hook registry is pre-computed once at import time. Executing hooks during a request is an **O(1)** lookup operation.
* **🧠 Intelligent Memory Management:** Uses **Sparse Snapshotting**—we only track fields that are actually watched. If you have a model with 50 fields but only watch `status`, we only cache `status`.
* **💎 Python 3.14+ & Django 5.2+ Ready:** Built strictly with modern typing (`Self`, `|` unions), `__slots__` optimizations, and native `transaction.on_commit` support.
* **🛡️ Type Safe:** 100% typed codebase ready for strict MyPy validation.

## Installation

```bash
pip install django-lifecycle-hooks
```

## Usage

```python
from django.db import models
from django_lifecycle_hooks import LifecycleModelMixin, hook, HookType

class UserAccount(LifecycleModelMixin, models.Model):
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="active")
    email_sent = models.BooleanField(default=False)
    login_count = models.IntegerField(default=0)

    # 1. Simple trigger: Run logic before saving
    @hook(HookType.BEFORE_SAVE)
    def clean_username(self):
        self.username = self.username.lower()

    # 2. Conditional trigger: Run only when status changes to 'banned'
    @hook(HookType.BEFORE_UPDATE, when="status", was="active", is_now="banned")
    def on_ban(self):
        print(f"Banning user {self.username}")
        self.email_sent = False
        # No need to call save(), we are in BEFORE_UPDATE

    # 3. Transaction aware: Run only after DB commit succeeds
    @hook(HookType.AFTER_SAVE, when="status", has_changed=True, on_commit=True)
    def notify_external_system(self):
        # Safe to launch async tasks or external API calls here
        print(f"Syncing status {self.status} to CRM...")
```

## ⚡ Performance Architecture

We take performance seriously. Here is how we differ from the rest:

| Feature | Legacy Libraries | Django Lifecycle Hooks |
| :--- | :--- | :--- |
| **Hook Resolution** | Runtime Introspection (Slow) | **Import-time Registry (Instant)** |
| **Change Detection** | Full `__dict__` copy (High RAM) | **Sparse Field Copy (Low RAM)** |
| **Data Structure** | Standard Dictionaries | **`__slots__` Optimized Classes** |
| **Async Support** | Limited / Hacky | **Native Django 5.x Compatibility** |

## ✨ Key Features

- **Granular Triggers:** `BEFORE_SAVE`, `AFTER_SAVE`, `BEFORE_CREATE`, `AFTER_CREATE`, `BEFORE_UPDATE`, `AFTER_UPDATE`, `BEFORE_DELETE`, `AFTER_DELETE`.
- **Smart Conditions:** Filter execution using `when`, `was`, `is_now`, and `has_changed`.
- **Transaction Safety:** Native `on_commit=True` support ensures your side effects (emails, tasks) only fire if the database transaction persists.
- **Developer Experience:** Auto-completion friendly and fully documented types.
