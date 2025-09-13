# Lazy-Core

[![PyPI](https://img.shields.io/pypi/v/lazy-core.svg)](https://pypi.org/project/lazy-core/)
[![CI](https://github.com/wrl96/lazy-core/actions/workflows/ci.yml/badge.svg)](https://github.com/wrl96/lazy-core/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/wrl96/lazy-core/branch/master/graph/badge.svg)](https://codecov.io/gh/wrl96/lazy-core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[中文文档](README_zh.md) | English

Lazy Family: [Lazy-Flask](https://github.com/wrl96/lazy-flask) | [Lazy-Django](https://github.com/wrl96/lazy-django) | [Lazy-FastAPI](https://github.com/wrl96/lazy-fastapi)

---

**Lazy-Core** is the core module of the `Lazy` framework family.
It provides modular registration, a unified request/response schema, middleware support, and consistent exception handling.

---

## Table of Contents
- [Installation (as a dependency)](#installation-as-a-dependency)
- [Module Overview](#module-overview)
- [Testing](#testing)
- [Code Style & Typing](#code-style--typing)
- [Contributing](#contributing)
- [License](#license)

---

## Installation (as a dependency)

It’s recommended to declare `lazy-core` as a dependency in your upper-layer framework/library. End users usually don’t need to install it directly.

```toml
# pyproject.toml
[tool.poetry.dependencies]
lazy-core = "^0.1.0"
```

Or install with pip:
```bash
pip install lazy-core
```

## Module Overview
- `LazyApp`：The core application class responsible for module management.
- `Module`：A modular unit that manages middleware and event handlers.
- `APIRequest`：A unified API request schema.
- `APIResponse`：A unified API response schema.
- `APIError`：A unified API error payload.
- `APIException`：The base exception for API errors.
- `Middleware`：Base class for middleware, supporting pre- and post-processing of requests.
- `LazyJSONEncoder`：JSON encoder tailored for the Lazy framework.

## Testing

This project ships with `pytest` and `coverage` reporting. Run all tests and generate an HTML report:

```bash
poetry run pytest --cov=lazy_core --cov-report=html
```

The coverage report will be available at `htmlcov/index.html`.

## Code Style & Typing

- Ruff (lint & auto-fix): `poetry run ruff check . --fix`
- MyPy (type checking): `poetry run mypy src/ tests/`
- pre-commit (run all hooks): `poetry run pre-commit run --all-files`

## Contributing

Issues and PRs are welcome! Please ensure:
- All lint/type/tests pass
- New features include corresponding tests
- The PR description is clear about the change

## License

This project is licensed under the MIT License.
