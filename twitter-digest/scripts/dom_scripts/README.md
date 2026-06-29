# DOM Scripts

These JavaScript snippets are loaded by `dom_script_loader.py` and executed in the X page through Chrome DevTools Protocol `Runtime.evaluate`.

Keep DOM-specific heuristics here instead of embedding long JavaScript strings inside Python. This keeps the Python collectors focused on browser orchestration, retries, normalization, and output, while the JavaScript files own page-specific selectors, layout thresholds, and text extraction.

Maintenance rules:

- Name visual thresholds and timing/window constants before using them.
- Keep selectors and i18n text markers close to the script that uses them.
- Return plain JSON-compatible values only: objects, arrays, strings, numbers, booleans, or null.
- Treat X DOM attributes such as `data-testid` as hints, not the only source of truth.
- Prefer readable helper predicates over long inline DOM conditions.
