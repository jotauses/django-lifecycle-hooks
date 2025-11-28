# Django Lifecycle Hooks

**The elegant, high-performance way to handle Django model events.**

[![PyPI version](https://img.shields.io/pypi/v/django-lifecycle-hooks.svg?color=2c3e50&labelColor=ecf0f1)](https://pypi.org/project/django-lifecycle-hooks/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-lifecycle-hooks.svg?color=2c3e50&labelColor=ecf0f1)](https://pypi.org/project/django-lifecycle-hooks/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-lifecycle-hooks.svg?color=2c3e50&labelColor=ecf0f1)](https://pypi.org/project/django-lifecycle-hooks/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2c3e50.svg?labelColor=ecf0f1)](https://opensource.org/licenses/MIT)

---

## 👋 Welcome

**Django Lifecycle Hooks** transforms how you write Django signals. Instead of scattering logic across multiple files and connecting signals manually, you declare your logic right where it belongs: **inside your model**.

It's designed to be:
- **Intuitive**: Read your code and know exactly what happens when.
- **Fast**: Zero runtime overhead for setup; optimized for speed.
- **Modern**: Built for Python 3.14+ and Django 5.2+, with full type safety.

## ✨ Why use this?

### 🚫 The Old Way (Signals)
```python
# signals.py
@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        ...
```
*Logic is separated from the model, hard to track, and often leads to circular imports.*

### ✅ The Lifecycle Way
```python
# models.py
class User(LifecycleModelMixin, models.Model):
    @hook(HookType.AFTER_CREATE)
    def send_welcome_email(self):
        ...
```
*Logic is co-located, readable, and declarative.*

## 🚀 Quick Start

### 1. Install
```bash
pip install django-lifecycle-hooks
```

### 2. Use
Inherit from `LifecycleModelMixin` and start decorating!

```python
from django.db import models
from django_lifecycle_hooks import LifecycleModelMixin, hook, HookType

class UserAccount(LifecycleModelMixin, models.Model):
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="active")

    @hook(HookType.BEFORE_SAVE)
    def clean_username(self):
        self.username = self.username.lower()

    @hook(HookType.AFTER_UPDATE, when="status", was="active", is_now="banned")
    def on_ban(self):
        print(f"User {self.username} has been banned.")
```

## 📚 Documentation

- [**User Guide**](user-guide.md): Learn the basics and master advanced patterns.
- [**API Reference**](api.md): Detailed technical documentation.

---
*Crafted with ❤️ for the Django community.*
