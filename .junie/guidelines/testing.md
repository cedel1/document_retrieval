# Testing Guidelines

## Test Naming Convention

All test functions must follow this format:

```
test_{method_name}_{should|should_not}_{what_is_being_checked}
```

### Rules

1. **Start with `test_`** — required by pytest discovery.
2. **Include the method name** being tested (e.g., `output_base`, `get_document_pages`, `init`).
3. **Use `should` or `should_not`** to indicate expected behavior.
4. **Describe what is being checked** in snake_case after the should/should_not.

### Examples

- `test_output_base_should_truncate_filename_to_64_chars`
- `test_get_document_pages_should_retry_with_next_method_on_failure`
- `test_init_should_raise_type_error_when_instantiated_directly`
- `test_set_next_getter_should_raise_value_error_when_no_more_getters`

### Why

This convention makes test failures self-documenting. When a test fails, the name immediately tells you which method, what behavior, and what condition was expected — without needing to read the test body.

## Exception Tests (Sonar python:S5778)

Only **one** call that can raise may be inside a `with pytest.raises(...)` block - otherwise it is unclear which call
raised and the test may pass by accident.

- Do all setup outside the block: constructing objects, building config files/paths, creating mocks, computing arguments.
- Inside the block put only the single call under test.
- Do not put two `pytest.raises` scenarios into one test; parametrize or split them.

```python
getter = SimpleDomGetterMethod({})  # setup outside

with pytest.raises(ValueError, match="Certificate validation failed"):
    getter.get_document_source(document_url)  # only the call under test
```

## General Test Style

- One behavior per test: do not assert two opposite outcomes in a single test; parametrize or split.
- Do not use `monkeypatch` in tests or fixtures. Use `unittest.mock.patch` / `patch.object` context managers
  (yielded from fixtures) or `responses` for HTTP.
- Move repeated setup into the area's `fixtures.py` (see `test/services/fixtures.py`) and import fixtures explicitly.
- Format with `black` and check with `pylint` (line length 120).
