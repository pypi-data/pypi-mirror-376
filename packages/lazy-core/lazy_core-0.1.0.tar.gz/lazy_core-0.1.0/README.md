# Lazy-Core

[![PyPI](https://img.shields.io/pypi/v/lazy-core.svg)](https://pypi.org/project/lazy-core/)
[![CI](https://github.com/wrl96/lazy-core/actions/workflows/ci.yml/badge.svg)](https://github.com/wrl96/lazy-core/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/wrl96/lazy-core/branch/master/graph/badge.svg)](https://codecov.io/gh/wrl96/lazy-core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

`Lazy-Core` 是lazy系列框架的核心模块，提供模块化注册、统一请求响应结构、中间件支持和异常处理等功能，旨在简化Python Web应用开发。

---

## 目录
- [模块说明](#模块说明)
- [安装](#安装仅供依赖集成)
- [测试](#测试)
- [代码风格与类型检查](#代码风格与类型检查)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 模块说明
- `Module`：模块注册与函数管理，支持多框架集成
- `APIRequest`/`APIResponse`：统一请求/响应结构，自动校验
- `Middleware`：中间件定义与优先级，支持多种类型
- `APIException`：统一异常处理

## 安装（仅供依赖集成）
建议由上层框架库在 `pyproject.toml` 里声明依赖，无需终端用户单独安装。

## 测试

项目已集成 pytest 和 coverage，运行所有测试并生成覆盖率报告：

```bash
poetry run pytest --cov=lazy_core --cov-report=html
```

覆盖率报告在 `htmlcov/index.html`。

## 代码风格与类型检查

- Ruff 检查：`poetry run ruff check . --fix`
- MyPy 检查：`poetry run mypy src/ tests/`
- pre-commit 检查：`poetry run pre-commit run --all-files`

## 贡献指南

欢迎提交 Issue 和 PR！请确保：
- 代码通过所有 lint/type/test 检查
- 新功能有对应测试
- PR 说明清晰

## 许可证

本项目采用 MIT License。
