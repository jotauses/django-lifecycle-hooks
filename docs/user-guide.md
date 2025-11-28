# User Guide

Welcome to the **Django Lifecycle Hooks** user guide. This document will take you from your first hook to mastering advanced lifecycle patterns.

---

## 🏁 Getting Started

### The Basics

To start using lifecycle hooks, you only need two things:
1.  Inherit from `LifecycleModelMixin`.
2.  Use the `@hook` decorator.

```python
from django_lifecycle_hooks import LifecycleModelMixin, hook, HookType

class Article(LifecycleModelMixin, models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField()

    @hook(HookType.BEFORE_SAVE)
    def generate_slug(self):
        if not self.slug:
            self.slug = slugify(self.title)
```

### Available Triggers

You can hook into any stage of the model's lifecycle:

| Trigger | Description |
| :--- | :--- |
| `BEFORE_SAVE` | Runs before any save (create or update). |
| `AFTER_SAVE` | Runs after any save. |
| `BEFORE_CREATE` | Runs only before creating a new record. |
| `AFTER_CREATE` | Runs only after creating a new record. |
| `BEFORE_UPDATE` | Runs only before updating an existing record. |
| `AFTER_UPDATE` | Runs only after updating an existing record. |
| `BEFORE_DELETE` | Runs before deleting a record. |
| `AFTER_DELETE` | Runs after deleting a record. |

---

## 🎯 Conditional Execution

Hooks become truly powerful when you control **when** they run.

### Watching Fields

You can tell a hook to run only when a specific field changes or matches a value.

```python
@hook(HookType.AFTER_UPDATE, when="status", was="draft", is_now="published")
def send_notifications(self):
    # Only runs when status changes from 'draft' to 'published'
    ...
```

**Available Arguments:**
- `when`: The field to watch.
- `has_changed`: `True` to run only if the value changed.
- `was`: Run only if the previous value matched this.
- `is_now`: Run only if the new value matches this.

### Watching Related Fields

You can even watch fields on related models using dot notation!

```python
class Book(LifecycleModelMixin, models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    @hook(HookType.BEFORE_SAVE, when="author.is_active", is_now=False)
    def warn_inactive_author(self):
        print("Warning: Assigning an inactive author.")
```

---

## ⚡ Async Support

Modern Django is async, and so are we. You can define `async` hooks and they will work seamlessly.

```python
@hook(HookType.AFTER_SAVE)
async def send_discord_notification(self):
    await self.discord_client.send_message(...)
```

> **Note:** To trigger async hooks, you must use `await instance.asave()` instead of `instance.save()`.

---

## 🛠️ Advanced Patterns

### Stacked Hooks

Need the same method to run on multiple events? Just stack the decorators.

```python
@hook(HookType.AFTER_CREATE)
@hook(HookType.AFTER_UPDATE, when="status", has_changed=True)
def update_search_index(self):
    ...
```

### Complex Conditions

For logic that goes beyond simple value matching, use **Advanced Conditions**.

```python
from django_lifecycle_hooks import WhenFieldHasChanged, WhenFieldValueIs

# Run if status changed AND category is 'VIP'
@hook(HookType.BEFORE_UPDATE, condition=WhenFieldHasChanged("status") & WhenFieldValueIs("category", "VIP"))
def notify_vip_manager(self):
    ...
```

### Hook Priority

If you have multiple hooks for the same trigger, you can control their order with `priority`. Higher numbers run first.

```python
@hook(HookType.BEFORE_SAVE, priority=10)
def run_first(self): ...

@hook(HookType.BEFORE_SAVE, priority=0)
def run_second(self): ...
```

### Skipping Hooks

Sometimes you need to save without triggering hooks (e.g., during data migrations).

```python
instance.save(skip_hooks=True)
```

---

## 🔍 Introspection

Need to see what hooks are registered on your models? We provide a handy management command:

```bash
python manage.py list_hooks
```

This will print a beautiful table showing all your hooks, their triggers, and conditions.

---

## 🛡️ System Checks

We include built-in system checks to catch common errors, like watching a field that doesn't exist. Run them with:

```bash
python manage.py check
```
