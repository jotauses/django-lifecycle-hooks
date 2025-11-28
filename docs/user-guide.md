# User Guide

Welcome to the **Django Lifecycle Hooks** user guide. This document is designed to take you from "Hello World" to mastering complex, high-performance lifecycle patterns.

---

## 🏁 Getting Started

### Installation

```bash
pip install django-lifecycle-hooks
```

### The Basics

To start using lifecycle hooks, you only need two things:
1.  Inherit from `LifecycleModelMixin`.
2.  Use the `@hook` decorator.

```python
from django.db import models
from django_lifecycle_hooks import LifecycleModelMixin, hook, HookType

class Article(LifecycleModelMixin, models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    status = models.CharField(max_length=20, default="draft")

    @hook(HookType.BEFORE_SAVE)
    def generate_slug(self):
        if not self.slug:
            self.slug = slugify(self.title)
```

---

## 🎯 Hook Triggers

The library supports all standard Django model events.

| Trigger | Description |
| :--- | :--- |
| `BEFORE_SAVE` | Runs before `save()`. Ideal for data validation or normalization. |
| `AFTER_SAVE` | Runs after `save()`. Ideal for side effects (emails, indexing). |
| `BEFORE_CREATE` | Runs before `save()`, but **only** if it's a new record. |
| `AFTER_CREATE` | Runs after `save()`, but **only** if it's a new record. |
| `BEFORE_UPDATE` | Runs before `save()`, but **only** if updating an existing record. |
| `AFTER_UPDATE` | Runs after `save()`, but **only** if updating an existing record. |
| `BEFORE_DELETE` | Runs before `delete()`. |
| `AFTER_DELETE` | Runs after `delete()`. |

---

## 🧠 Conditional Execution

The real power of this library lies in its ability to run hooks **only when specific conditions are met**.

### Simple Conditions (Arguments)

You can filter execution using arguments directly in the `@hook` decorator.

#### 1. `when` (Field Watching)
Run only if a specific field is involved.

```python
@hook(HookType.BEFORE_SAVE, when="status")
def on_status_touch(self):
    print("Status field is being saved!")
```

#### 2. `has_changed`
Run only if the field's value has actually changed.

```python
@hook(HookType.BEFORE_SAVE, when="status", has_changed=True)
def on_status_change(self):
    # Runs if status goes from 'draft' -> 'published'
    # Does NOT run if status goes from 'draft' -> 'draft'
    pass
```

#### 3. `was` and `is_now` (Value Matching)
Run only if the field matches specific values.

```python
@hook(HookType.AFTER_UPDATE, when="status", was="draft", is_now="published")
def publish_article(self):
    print("Article just got published!")
```

### Advanced Conditions (Classes)

For complex logic, use Condition classes. You can combine them using logical operators: `&` (AND), `|` (OR), `~` (NOT).

```python
from django_lifecycle_hooks import (
    WhenFieldHasChanged, 
    WhenFieldValueIs, 
    WhenFieldValueChangesTo
)

class Order(LifecycleModelMixin, models.Model):
    status = models.CharField(...)
    is_paid = models.BooleanField(...)

    # Run if status changes to 'shipped' AND the order is paid
    @hook(HookType.AFTER_SAVE, condition=(
        WhenFieldValueChangesTo("status", "shipped") & 
        WhenFieldValueIs("is_paid", True)
    ))
    def ship_order(self):
        ...
```

**Available Conditions:**
- `WhenFieldHasChanged(field)`
- `WhenFieldValueIs(field, value)`
- `WhenFieldValueIsNot(field, value)`
- `WhenFieldValueWas(field, value)`
- `WhenFieldValueWasNot(field, value)`
- `WhenFieldValueChangesTo(field, value)`

---

## ⚡ Async & ASGI Support

We are the **only** lifecycle library with first-class Async support.

### Using `asave` and `acreate`
When you use Django's async methods, your hooks run automatically.

```python
# This will trigger all your hooks, just like synchronous save()
await article.asave()
await Article.objects.acreate(title="Async Article")
```

### Writing Async Hooks
You can define hooks as `async def`. They will be awaited properly when using `asave()`.

```python
@hook(HookType.AFTER_SAVE)
async def send_notification(self):
    # Fully non-blocking!
    await email_service.send_async(...)
```

> **Note:** If you call `save()` (sync) on a model with async hooks, the async hooks are **skipped** to prevent runtime errors. Always use `asave()` if you have async logic.

---

## 🛡️ Transaction Safety

Side effects like sending emails or charging credit cards should only happen if the database transaction succeeds.

Use `on_commit=True` to defer execution until the transaction commits.

```python
@hook(HookType.AFTER_SAVE, on_commit=True)
def charge_card(self):
    # This runs ONLY after the DB transaction is fully committed.
    payment_gateway.charge(...)
```

---

## 🔍 Inspecting State

Sometimes you need to check state manually inside your methods.

```python
def my_custom_logic(self):
    if self.has_changed("status"):
        old = self.initial_value("status")
        new = self.current_value("status")
        print(f"Changed from {old} to {new}")
```

- `self.has_changed(field)`: Returns `True` if the field changed.
- `self.initial_value(field)`: Returns the value from when the instance was loaded.
- `self.current_value(field)`: Returns the current value.

---

## 🛠️ Advanced Patterns

### Watching Related Fields
You can watch fields on related models using dot notation.

```python
class Book(LifecycleModelMixin, models.Model):
    author = models.ForeignKey(Author, ...)

    # Runs if the author's name changes!
    @hook(HookType.BEFORE_SAVE, when="author.name", has_changed=True)
    def on_author_rename(self):
        ...
```

### Stacked Hooks
You can attach multiple hooks to the same method.

```python
@hook(HookType.AFTER_CREATE)
@hook(HookType.AFTER_UPDATE, when="status", has_changed=True)
def update_search_index(self):
    # Runs on creation OR when status changes
    index.update(self)
```

### Suppressing Hooks
Need to bulk update without triggering hooks? Use the context manager.

```python
with instance.suppress_hooked_methods():
    instance.status = "maintenance"
    instance.save()  # No hooks will fire
```

### Introspection
See exactly what hooks are registered on your model.

```bash
python manage.py list_hooks
```

---

## ⚠️ Common Gotchas

1.  **`update_fields` Optimization**: If you save with `save(update_fields=['status'])`, hooks watching other fields (e.g., `title`) will be **skipped** for performance.
2.  **Bulk Operations**: Django's `queryset.update()` and `queryset.bulk_create()` do **NOT** call `save()`, so they do **NOT** trigger hooks. This is standard Django behavior.
3.  **Async Mixing**: Async hooks (`async def`) only run during `asave()`. Sync hooks (`def`) run during both `save()` and `asave()`.
