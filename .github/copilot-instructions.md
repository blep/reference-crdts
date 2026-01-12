# GitHub Copilot Instructions for Reference CRDT

## Project Overview

This is a port to type annotated Python 3.13 of reference CRDT implement made in Typescript.

**Technology Stack**:
- Python 3.13+ with type annotations
- pytest for testing

## Coding Style and Conventions

### Error Handling

- Prefer letting exceptions propagate rather than hiding them
- Use production-quality error handling (no silent failures)

### Code Structure & Style

- Write well-structured, production-quality code that is easy to read
- **Don't reference fields or methods prefixed with underscore (`_`)** on unrelated classes - these are protected implementation details
- **Prefer returning frozen dataclasses instead of tuples** for public APIs
- **Don't use local imports** - they hide dependencies and often indicate module dependency cycles (which are not allowed)
- **Keep `__init__.py` files empty (with only docstring)** - avoid re-exporting symbols to prevent circular dependencies; import directly from specific modules instead
- **Python convention: represent time/delay as seconds (float)**
- **Rethink code to avoid deep nesting** - prefer early returns when it doesn't duplicate code
- **Use named column access for database rows** - prefer `row['column_name']` over `row[0]` for better readability and maintainability
- Don't remove existing docstrings/comments unless specifically instructed
- Don't add context-dependent comments that won't make sense later
- No dead code (commented-out code)
- Use the chat to explain changes and rationale behind design decisions
- **IMPORTANT: Always minimize changes to make review easier**

### Testing

- Use pytest with modern Python style, leveraging pytest's well-known features
- Tests are located in `tests/` directory and named with `_test` suffix (e.g., `src/collabdb/db.py` → `tests/db_test.py`)
- Use fixtures for database isolation
- Temporary paths for test database files
- Test data models, filtering logic, and core business logic
- Don't test implementation details directly (focus on observable behavior)

### File Management

- The project uses git for versioning
- When creating new files or renaming them, use IDE integration features so git is aware of the changes
- Ensure git tracks all source code changes properly
