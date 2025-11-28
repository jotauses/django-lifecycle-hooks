# API Reference

This section provides detailed technical documentation for the `django-lifecycle-hooks` API.

---

## 🧩 Decorators

### `@hook`

The core decorator used to register lifecycle methods.

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

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `trigger` | `HookType` | **Required** | The lifecycle event to hook into (e.g., `HookType.BEFORE_SAVE`). |
| `when` | `str` | `None` | The field name to watch. Supports dot notation (e.g., `"author.name"`). |
| `was` | `Any` | `"*"` | Execute only if the field's **previous** value matches this. `"*"` means any value. |
| `is_now` | `Any` | `"*"` | Execute only if the field's **current** value matches this. `"*"` means any value. |
| `has_changed` | `bool` | `False` | If `True`, execute only if the field's value has changed. |
| `condition` | `Condition` | `None` | An advanced condition object (e.g., `WhenFieldHasChanged(...)`). |
| `priority` | `int` | `0` | Execution order. Higher values run first. |
| `on_commit` | `bool` | `False` | If `True`, the hook runs only after the transaction commits successfully. |

---

## 🏗️ Mixins

### `LifecycleModelMixin`

The base mixin that enables lifecycle hooks on your Django models.

#### Methods

##### `has_changed(field_name: str) -> bool`
Checks if a field has changed since the instance was loaded or last saved.
- **Note**: Only works for fields that are being watched by at least one hook (Sparse Snapshotting).

##### `initial_value(field_name: str) -> Any`
Returns the value of the field as it was when the instance was loaded.

##### `current_value(field_name: str) -> Any`
Returns the current value of the field on the instance.

##### `suppress_hooked_methods()`
A context manager to temporarily disable all lifecycle hooks for the instance.

```python
with instance.suppress_hooked_methods():
    instance.save()
```

---

## 🚦 Enums

### `HookType`

Defines the available lifecycle events.

- `BEFORE_SAVE`
- `AFTER_SAVE`
- `BEFORE_CREATE`
- `AFTER_CREATE`
- `BEFORE_UPDATE`
- `AFTER_UPDATE`
- `BEFORE_DELETE`
- `AFTER_DELETE`

---

## 🧠 Conditions

Condition classes allow for complex logic. They support logical operators: `&` (AND), `|` (OR), `~` (NOT).

### `WhenFieldHasChanged`
Checks if a field's value has changed.
```python
WhenFieldHasChanged(field_name: str)
```

### `WhenFieldValueIs`
Checks if a field's **current** value equals the given value.
```python
WhenFieldValueIs(field_name: str, value: Any)
```

### `WhenFieldValueIsNot`
Checks if a field's **current** value does **not** equal the given value.
```python
WhenFieldValueIsNot(field_name: str, value: Any)
```

### `WhenFieldValueWas`
Checks if a field's **initial** value equals the given value.
```python
WhenFieldValueWas(field_name: str, value: Any)
```

### `WhenFieldValueWasNot`
Checks if a field's **initial** value does **not** equal the given value.
```python
WhenFieldValueWasNot(field_name: str, value: Any)
```

### `WhenFieldValueChangesTo`
Checks if a field has changed **AND** its new value equals the given value.
```python
WhenFieldValueChangesTo(field_name: str, value: Any)
```
