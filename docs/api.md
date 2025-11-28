# API Reference

## 🧩 Decorators

### `@hook`

The core decorator for registering lifecycle methods.

```python
def hook(
    trigger: HookType,
    when: str | None = None,
    was: Any = "*",
    is_now: Any = "*",
    has_changed: bool = False,
    condition: Any = None,
    priority: int = 0,
    on_commit: bool = False,
)
```

**Parameters:**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `trigger` | `HookType` | The lifecycle event to hook into (e.g., `HookType.BEFORE_SAVE`). |
| `when` | `str` | Optional field name to watch. Supports dot notation for related fields (e.g., `"author.name"`). |
| `was` | `Any` | Execute only if the field's **previous** value matches this. Defaults to `"*"` (any). |
| `is_now` | `Any` | Execute only if the field's **current** value matches this. Defaults to `"*"` (any). |
| `has_changed` | `bool` | If `True`, execute only if the field's value has changed. |
| `condition` | `Condition` | An advanced condition object (e.g., `WhenFieldHasChanged(...)`). |
| `priority` | `int` | Execution order. Higher values run first. Default is `0`. |
| `on_commit` | `bool` | If `True`, the hook runs only after the transaction commits successfully. |

---

## 🧬 Mixins

### `LifecycleModelMixin`

The mixin that powers the lifecycle hooks. Inherit from this in your Django models.

**Methods:**

#### `has_changed(field_name: str) -> bool`
Checks if a specific field has changed since the model was instantiated or last saved.

#### `initial_value(field_name: str) -> Any`
Returns the value of the field as it was when the instance was loaded from the database.

#### `current_value(field_name: str) -> Any`
Returns the current value of the field on the instance.

#### `suppress_hooked_methods() -> ContextManager`
A context manager to temporarily disable all lifecycle hooks for the instance.

```python
with instance.suppress_hooked_methods():
    instance.save()  # No hooks will run
```

---

## 🎛️ Conditions

Advanced condition classes for complex logic. These can be combined using `&` (AND), `|` (OR), and `~` (NOT).

| Class | Description |
| :--- | :--- |
| `WhenFieldHasChanged(field)` | True if the field has changed. |
| `WhenFieldValueIs(field, value)` | True if current value equals `value`. |
| `WhenFieldValueIsNot(field, value)` | True if current value does **not** equal `value`. |
| `WhenFieldValueWas(field, value)` | True if initial value equaled `value`. |
| `WhenFieldValueWasNot(field, value)` | True if initial value did **not** equal `value`. |
| `WhenFieldValueChangesTo(field, value)` | True if field changed **and** new value equals `value`. |

**Example:**
```python
condition = WhenFieldHasChanged("status") & ~WhenFieldValueIs("type", "draft")
```
