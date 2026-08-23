<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-crypto ✨
[![LICENSE](https://img.shields.io/github/license/ByteColtX/nonebot-plugin-crypto.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-crypto.svg)](https://pypi.python.org/pypi/nonebot-plugin-crypto)
[![python](https://img.shields.io/badge/python-3.10--3.14-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/ByteColtX/nonebot-plugin-crypto/master.svg)](https://results.pre-commit.ci/latest/github/ByteColtX/nonebot-plugin-crypto/master)

</div>

## 📖 介绍

基于 Binance Public API 的 NoneBot 加密货币行情插件，支持实时行情和交易对列表查询。
插件仅使用 `/crypto` 作为行情查询命令，CI 验证 Python 3.10 至 3.14。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-crypto --upgrade
使用 **pypi** 源安装

    nb plugin install nonebot-plugin-crypto --upgrade -i "https://pypi.org/simple"
使用**清华源**安装

    nb plugin install nonebot-plugin-crypto --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"


</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-crypto
安装仓库 master 分支

    uv add git+https://github.com/ByteColtX/nonebot-plugin-crypto@master
</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-crypto
安装仓库 master 分支

    pdm add git+https://github.com/ByteColtX/nonebot-plugin-crypto@master
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-crypto
安装仓库 master 分支

    poetry add git+https://github.com/ByteColtX/nonebot-plugin-crypto@master
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_crypto"]

</details>

<details>
<summary>使用 nbr 安装(使用 uv 管理依赖可用)</summary>

[nbr](https://github.com/fllesser/nbr) 是一个基于 uv 的 nb-cli，可以方便地管理 nonebot2

    nbr plugin install nonebot-plugin-crypto
使用 **pypi** 源安装

    nbr plugin install nonebot-plugin-crypto -i "https://pypi.org/simple"
使用**清华源**安装

    nbr plugin install nonebot-plugin-crypto -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>


## ⚙️ 配置

本插件使用 Binance Public API，无需配置 API Key、Secret 或 Access Token。请勿将个人
配置、代理信息或其他敏感信息提交到代码仓库。

## 🎉 使用

### 指令表

| 指令 | 权限 | 需要@ | 范围 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `/crypto <SYMBOL>` | 群员 | 否 | 群聊、私聊 | 查询加密货币实时行情 |
| `/crypto list [KEYWORD]` | 群员 | 否 | 群聊、私聊 | 查询 Binance Spot 交易对列表 |

输入 `/crypto --help` 可以查看完整帮助信息。

### 实时行情

```text
/crypto BTC
/crypto ETHUSDT
/crypto SOL/USDT
```

### 交易对列表

```text
/crypto list
/crypto list btc
/crypto list usdt
```

列表数据来自 Binance Spot 交易所，默认只返回状态为 `TRADING` 的交易对，并通过合并转发发送结果。

### 热门币种快捷查询

插件内置了一次性获取的 Binance Spot USDT 交易对成交额 Top 20 快照。直接发送榜单中的基础币种，
例如 `XRP`，即可查询对应行情；榜单不会在运行时自动更新。

### 🎨 效果图

暂无示例图。
