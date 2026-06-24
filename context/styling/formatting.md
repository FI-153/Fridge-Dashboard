# Code Style Guide

## Python

### Naming

- **Classes**: `PascalCase` (e.g., `HassClient`, `Config`)
- **Functions / methods**: `snake_case` (e.g., `get_state`, `build_dashboard_model`)
- **Constants / module-level config**: `UPPER_SNAKE_CASE` (e.g., `CONFIG`, `_REQUIRED`)
- **Private attributes / helpers**: prefix with `_` (e.g., `self._base`, `_reading`)

### Docstrings

Google-style docstrings on all public functions, methods, and classes:

```python
def get_state(self, entity_id: str) -> dict:
    """
    Fetches the state and unit of a Home Assistant entity.

    Args:
      entity_id (str): The entity ID to fetch.

    Returns:
      dict: {"result": "OK", "state": str, "unit": str | None} on success,
          otherwise {"result": "err"}.
    """
```

- Indent docstring body with 4 spaces.
- Include `Args:` when the function takes parameters beyond `self`.
- Always include `Returns:` (and `Raises:` when applicable).

### Indentation & formatting

- 4-space indentation (PEP 8). Enforced by ruff (`make lint` / `make format`).
- Line length 120.

### Imports

- Standard library first, then third-party, then local modules.
- Explicit imports everywhere (no `import *`).

## HTML / Templates

- Jinja2 templates live in `templates/`. The shared `<head>` is `_head.html`,
  included by each page.
- Use `url_for('static', ...)` for asset URLs.
- Keep markup minimal and table/flexbox-based for Safari 9 compatibility.

## CSS

- Class and ID names use `snake_case` (e.g., `metric_card`, `split_half`).
- **Dark theme only.**
- **Flexbox is allowed; CSS Grid and CSS custom properties (`var()`) are NOT** —
  they are unsupported on the target Safari 9. Include `-webkit-` prefixes for
  flexbox properties.
- No `calc()`-dependent layouts that assume modern engines; keep it simple.

## JavaScript

- **ES5 only** (the iPad mini 1 runs Safari 9). No `let`/`const`/arrow functions/
  template literals. Wrap in an IIFE; no external dependencies.

## Tests

- pytest, written test-first (TDD). Mock `requests` at the module boundary
  (`homeassistant.client.requests.get`), not deeper.
