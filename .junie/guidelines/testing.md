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
