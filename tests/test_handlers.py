from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nonebot.adapters.onebot.v11 import Message

import nonebot_plugin_crypto
from fake import fake_group_message_event_v11
from nonebot_plugin_crypto import handlers
from nonebot_plugin_crypto.constants import HELP_TEXT


class MatcherFinished(Exception):
    """捕获 matcher.finish，便于直接测试 handler 的最终消息。"""

    def __init__(self, message: object = None) -> None:
        super().__init__(message)
        self.message = message


@pytest.fixture
def finish_matchers(monkeypatch: pytest.MonkeyPatch) -> None:
    """把 matcher.finish 替换成可断言的异常。"""

    async def finish(message: object = None, **_kwargs: object) -> None:
        raise MatcherFinished(message)

    for matcher in (handlers.market_command,):
        monkeypatch.setattr(matcher, "finish", finish)


def test_package_entrypoint_registers_only_crypto_handler() -> None:
    assert handlers.market_command.handlers
    assert "cmds=(('crypto',),)" in repr(handlers.market_command.rule)
    assert not hasattr(handlers, "market_list_command")
    assert not hasattr(handlers, "popular_market")


def test_package_entrypoint_declares_nonebot_plugin_metadata() -> None:
    metadata = nonebot_plugin_crypto.__plugin_meta__

    assert metadata.name == "加密货币行情"
    assert metadata.description == (
        "基于 Binance Public API 的加密货币实时行情和交易对列表插件。"
    )
    assert metadata.usage == (
        "/crypto <symbol> 查询实时行情；/crypto list [keyword] 查询交易对列表。"
    )
    assert metadata.type == "application"
    assert metadata.homepage == "https://github.com/ByteColtX/nonebot-plugin-crypto"
    assert metadata.supported_adapters == {"~onebot.v11"}


@pytest.mark.asyncio
async def test_handle_market_command_supports_help_and_valid_symbol(
    monkeypatch: pytest.MonkeyPatch, finish_matchers: None
) -> None:
    with pytest.raises(MatcherFinished) as help_finished:
        await handlers.handle_market_command(
            SimpleNamespace(), SimpleNamespace(), Message("--help")
        )
    assert help_finished.value.message == HELP_TEXT

    reply = "BTC/USDT Market Data"
    build_reply = AsyncMock(return_value=reply)
    monkeypatch.setattr(handlers, "build_market_reply", build_reply)
    with pytest.raises(MatcherFinished) as market_finished:
        await handlers.handle_market_command(
            SimpleNamespace(), SimpleNamespace(), Message(" btc ")
        )
    assert market_finished.value.message == reply
    build_reply.assert_awaited_once_with("BTCUSDT")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        ("", "用法：/crypto <symbol>，例如：/crypto BTC、/crypto ETHUSDT"),
        ("BTC ETH", "用法：/crypto <symbol>，例如：/crypto BTC、/crypto ETHUSDT"),
        ("USDT", "❌ symbol 格式无效，例如：BTC、ETHUSDT、SOL/USDT"),
    ],
)
async def test_handle_market_command_validates_arguments(
    finish_matchers: None, argument: str, expected: str
) -> None:
    with pytest.raises(MatcherFinished) as finished:
        await handlers.handle_market_command(
            SimpleNamespace(), SimpleNamespace(), Message(argument)
        )

    assert finished.value.message == expected


@pytest.mark.asyncio
async def test_handle_market_command_list_sends_forward_and_rejects_extra_args(
    monkeypatch: pytest.MonkeyPatch, finish_matchers: None
) -> None:
    send_list = AsyncMock(return_value=None)
    monkeypatch.setattr(handlers, "send_market_list", send_list)
    event = fake_group_message_event_v11()
    bot = SimpleNamespace()

    with pytest.raises(MatcherFinished) as listed:
        await handlers.handle_market_command(bot, event, Message("list btc"))
    assert listed.value.message is None
    send_list.assert_awaited_once_with(bot, event, "btc")

    with pytest.raises(MatcherFinished) as usage:
        await handlers.handle_market_command(bot, event, Message("list btc usdt"))
    assert usage.value.message == "用法：/crypto list [keyword]"
