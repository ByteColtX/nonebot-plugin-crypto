# AGENTS.md

本文件为在本仓库中工作的 coding agent 提供最少且必要的项目约定。以
`pyproject.toml`、源码和测试的实际行为为准；不要把通用模板内容带入本项目。

## 项目概况

- 本项目是 Python 3.10 的 NoneBot 插件，使用 `uv` 管理环境和依赖。
- Python 版本由 `.python-version` 和 `pyproject.toml` 固定为 3.10；不要使用其他
  Python 版本创建项目环境。
- 当前待迁移的插件实现位于项目根目录 `crypto.py`；目标包目录为
  `src/nonebot_plugin_crypto/`。后续迁移时，应将实现放入目标包并同步补充测试。
- 测试应位于 `tests/`，文件命名为 `test_<module>.py`。Binance 网络请求必须使用
  mock，测试不得依赖真实网络、账号或密钥。
- 不得把凭证、个人配置或运行时数据写入代码库。

## 开发与验证

所有 Python 命令均使用 `uv` 执行，不直接使用 `python`、`pip` 或 `pipx`。

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
```

修改代码后至少运行相关测试和 `uv run ruff check .`；涉及格式时再运行
`uv run ruff format .`。完整覆盖率测试使用项目已配置的任务：

```bash
uv run poe test
```

## 代码约定

- 遵循 Google Python Style Guide，行宽以 Ruff 配置的 88 个字符为准。
- 新增或修改的公共函数、方法和类必须有 Google 风格 docstring；函数参数和返回值
  必须有类型注解。私有函数可使用单行 docstring。
- 异步请求必须设置合理的超时，并在边界处处理 HTTP、网络和数据格式异常。
- 修改功能时同步更新测试；不要为了让测试通过而放宽生产代码的校验或错误处理。

## Git 提交

提交信息使用 Conventional Commits，标题和 body 均使用中文，例如：
`feat(crypto): 增加币价查询命令`。常用类型为 `feat`、`fix`、`docs`、`test`、
`refactor`、`perf` 和 `chore`。提交前确保测试、Ruff 和 pre-commit 检查通过；除非
用户明确要求，不自动创建提交。
