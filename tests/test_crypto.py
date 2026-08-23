from types import SimpleNamespace
from unittest.mock import AsyncMock

import crypto
import httpx
import pytest
from nonebot.adapters.onebot.v11 import Message

from fake import fake_group_message_event_v11, fake_private_message_event_v11


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

    for matcher in (
        crypto.market_command,
        crypto.market_list_command,
        crypto.popular_market,
    ):
        monkeypatch.setattr(matcher, "finish", finish)


@pytest.fixture(autouse=True)
def reset_exchange_info_cache() -> None:
    """避免交易对缓存污染不同测试。"""
    crypto._exchange_info_cache.expires_at = 0
    crypto._exchange_info_cache.symbols = ()


@pytest.mark.parametrize(
    ("value", "places", "signed", "expected"),
    [
        (None, 2, False, "-"),
        ("", 2, False, "-"),
        ("1234.5", 2, False, "1,234.50"),
        ("1.2", 2, True, "+1.20"),
        ("-1.2", 1, True, "-1.2"),
        ("unknown", 2, False, "unknown"),
    ],
)
def test_format_decimal(
    value: object, places: int, signed: bool, expected: str
) -> None:
    assert crypto._format_decimal(value, places, signed=signed) == expected


def test_format_time_converts_utc_to_shanghai_and_handles_invalid_values() -> None:
    assert crypto._format_time(0) == "1970-01-01 08:00:00"
    assert crypto._format_time("bad") == "-"
    assert crypto._format_time(None) == "-"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" btc ", "BTCUSDT"),
        ("SOL/USDT", "SOLUSDT"),
        ("eth-usdt", "ETHUSDT"),
        ("xrp", "XRPUSDT"),
        ("DOGEUSDC", "DOGEUSDC"),
        ("BTCUSDT", "BTCUSDT"),
        ("USDT", None),
        ("bad symbol", None),
        ("", None),
    ],
)
def test_normalize_symbol(value: str, expected: str | None) -> None:
    assert crypto._normalize_symbol(value) == expected


def test_split_symbol_prefers_longest_quote_asset() -> None:
    assert crypto._split_symbol("BTCUSDT") == ("BTC", "USDT")
    assert crypto._split_symbol("ETHBTC") == ("ETH", "BTC")
    assert crypto._split_symbol("UNKNOWN") == ("UNKNOWN", "")


def test_search_symbols_matches_symbol_base_quote_and_alias() -> None:
    symbols = (
        {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT"},
        {"symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC"},
        {"symbol": "SOLUSDC", "baseAsset": "SOL", "quoteAsset": "USDC"},
    )

    assert len(crypto._search_symbols(symbols, "btc")) == 2
    assert crypto._search_symbols(symbols, "sol/usdc") == (symbols[2],)
    assert len(crypto._search_symbols(symbols, "usdt")) == 1
    assert crypto._search_symbols(symbols, "missing") == ()
    assert crypto._search_symbols(symbols, "") == symbols


def test_build_forward_nodes_chunks_lines_and_uses_bot_identity() -> None:
    nodes = crypto._build_forward_nodes([str(index) for index in range(51)], "42")

    assert len(nodes) == 2
    assert nodes[0]["data"]["user_id"] == "42"
    assert nodes[0]["data"]["nickname"] == "Crypto Market"
    assert nodes[0]["data"]["content"][0]["data"]["text"].splitlines() == [
        str(index) for index in range(50)
    ]
    assert nodes[1]["data"]["content"][0]["data"]["text"] == "50"


class FakeResponse:
    def __init__(self, payload: object, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.status_code = 200

    def raise_for_status(self) -> None:
        if self.error:
            raise self.error

    def json(self) -> object:
        return self.payload


class FakeAsyncClient:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, object, object]] = []

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def get(
        self, url: str, *, params: object = None, headers: object = None
    ) -> FakeResponse:
        self.calls.append((url, params, headers))
        return self.response


@pytest.mark.asyncio
async def test_fetch_ticker_data_sends_symbol_and_accept_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = FakeResponse({"symbol": "BTCUSDT", "lastPrice": "100"})
    client = FakeAsyncClient(response)
    monkeypatch.setattr(crypto.httpx, "AsyncClient", lambda **_kwargs: client)

    result = await crypto._fetch_ticker_data("BTCUSDT")

    assert result["symbol"] == "BTCUSDT"
    assert client.calls == [
        (
            crypto.BINANCE_TICKER_URL,
            {"symbol": "BTCUSDT"},
            {"Accept": "application/json"},
        )
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], {"symbol": "ETHUSDT"}])
async def test_fetch_ticker_data_rejects_unexpected_payload(
    monkeypatch: pytest.MonkeyPatch, payload: object
) -> None:
    client = FakeAsyncClient(FakeResponse(payload))
    monkeypatch.setattr(crypto.httpx, "AsyncClient", lambda **_kwargs: client)

    with pytest.raises(TypeError):
        await crypto._fetch_ticker_data("BTCUSDT")


@pytest.mark.asyncio
async def test_fetch_exchange_symbols_filters_trading_and_caches_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "symbols": [
            {"symbol": "BTCUSDT", "status": "TRADING"},
            {"symbol": "OLDUSDT", "status": "BREAK"},
            "invalid",
        ]
    }
    client = FakeAsyncClient(FakeResponse(payload))
    monkeypatch.setattr(crypto.httpx, "AsyncClient", lambda **_kwargs: client)

    first = await crypto._fetch_exchange_symbols()
    second = await crypto._fetch_exchange_symbols()

    assert first == ({"symbol": "BTCUSDT", "status": "TRADING"},)
    assert second is first
    assert len(client.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], {"symbols": []}, {"symbols": "bad"}])
async def test_fetch_exchange_symbols_rejects_invalid_payload(
    monkeypatch: pytest.MonkeyPatch, payload: object
) -> None:
    client = FakeAsyncClient(FakeResponse(payload))
    monkeypatch.setattr(crypto.httpx, "AsyncClient", lambda **_kwargs: client)

    with pytest.raises((TypeError, ValueError)):
        await crypto._fetch_exchange_symbols()


@pytest.mark.asyncio
async def test_send_forward_market_list_supports_group_and_private(
    finish_matchers: None,
) -> None:
    group_bot = SimpleNamespace(self_id="7", call_api=AsyncMock())
    await crypto._send_forward_market_list(
        group_bot,
        fake_group_message_event_v11(group_id=42),
        ["header", "item"],
    )
    assert group_bot.call_api.await_args.args[0] == "send_group_forward_msg"
    assert group_bot.call_api.await_args.kwargs["group_id"] == 42

    private_bot = SimpleNamespace(self_id="7", call_api=AsyncMock())
    await crypto._send_forward_market_list(
        private_bot,
        fake_private_message_event_v11(user_id=24),
        ["content"],
    )
    assert private_bot.call_api.await_args.args[0] == "send_private_forward_msg"
    assert private_bot.call_api.await_args.kwargs["user_id"] == 24


@pytest.mark.asyncio
async def test_send_market_list_formats_matches_and_handles_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    symbols = (
        {"symbol": "BTCUSDT", "status": "TRADING"},
        {"symbol": "ETHUSDT", "status": "TRADING"},
    )
    send = AsyncMock()
    monkeypatch.setattr(
        crypto, "_fetch_exchange_symbols", AsyncMock(return_value=symbols)
    )
    monkeypatch.setattr(crypto, "_send_forward_market_list", send)
    event = fake_group_message_event_v11()
    bot = SimpleNamespace(self_id="1")

    assert await crypto._send_market_list(bot, event, "btc") is None
    assert send.await_args.args[2] == [
        "Binance Spot Trading Pairs · Search: BTC",
        "Status: TRADING | Matched: 1",
        "",
        "0001. BTCUSDT",
    ]
    assert await crypto._send_market_list(bot, event, "missing") == (
        "❌ 没有找到匹配的交易对：missing"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx.TimeoutException("timeout"), "❌ Binance 行情列表请求超时，请稍后再试"),
        (httpx.HTTPError("bad"), "❌ Binance 行情列表获取失败，请稍后再试"),
        (TypeError(), "❌ Binance 行情列表获取失败，请稍后再试"),
    ],
)
async def test_send_market_list_maps_fetch_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, expected: str
) -> None:
    monkeypatch.setattr(
        crypto,
        "_fetch_exchange_symbols",
        AsyncMock(side_effect=error),
    )

    result = await crypto._send_market_list(
        SimpleNamespace(), fake_group_message_event_v11(), ""
    )

    assert result == expected


def make_ticker(**overrides: object) -> dict[str, object]:
    """创建完整的 Binance 24 小时 ticker mock 数据。"""
    data: dict[str, object] = {
        "symbol": "BTCUSDT",
        "lastPrice": "1234.5",
        "priceChange": "12.5",
        "priceChangePercent": "1.02",
        "highPrice": "1300",
        "lowPrice": "1200",
        "volume": "123.4567",
        "quoteVolume": "987654.3",
        "closeTime": "0",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_build_market_reply_formats_ticker_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        crypto,
        "_fetch_ticker_data",
        AsyncMock(return_value=make_ticker()),
    )

    result = await crypto._build_market_reply("BTCUSDT")

    assert result == "\n".join(
        [
            "BTC/USDT Market Data",
            "Last Price: 1,234.50 USDT",
            "24h Change: +12.50 USDT (1.02%)",
            "24h High: 1,300.00 USDT",
            "24h Low: 1,200.00 USDT",
            "24h Volume: 123.457 BTC",
            "24h Amount: 987,654.30 USDT",
            "Time: 1970-01-01 08:00:00 (GMT+8)",
            "Source: Binance",
        ]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx.TimeoutException("timeout"), "❌ 行情请求超时，请稍后再试"),
        (TypeError(), "❌ 行情获取失败，请稍后再试"),
        (ValueError(), "❌ 行情获取失败，请稍后再试"),
    ],
)
async def test_build_market_reply_maps_non_http_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, expected: str
) -> None:
    monkeypatch.setattr(crypto, "_fetch_ticker_data", AsyncMock(side_effect=error))

    assert await crypto._build_market_reply("BTCUSDT") == expected


@pytest.mark.asyncio
async def test_build_market_reply_maps_binance_http_status_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_request = httpx.Response(400, request=httpx.Request("GET", "https://test"))
    server_error = httpx.Response(500, request=httpx.Request("GET", "https://test"))

    monkeypatch.setattr(
        crypto,
        "_fetch_ticker_data",
        AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "bad", request=bad_request.request, response=bad_request
            )
        ),
    )
    assert await crypto._build_market_reply("BTCUSDT") == (
        "❌ 未找到可用的 Binance 现货交易对：BTCUSDT"
    )

    monkeypatch.setattr(
        crypto,
        "_fetch_ticker_data",
        AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "bad", request=server_error.request, response=server_error
            )
        ),
    )
    assert await crypto._build_market_reply("BTCUSDT") == (
        "❌ Binance 行情接口返回错误：500"
    )


@pytest.mark.asyncio
async def test_handle_market_command_supports_help_and_valid_symbol(
    monkeypatch: pytest.MonkeyPatch, finish_matchers: None
) -> None:
    with pytest.raises(MatcherFinished) as help_finished:
        await crypto.handle_market_command(
            SimpleNamespace(), SimpleNamespace(), Message("--help")
        )
    assert help_finished.value.message == crypto.HELP_TEXT

    reply = "BTC/USDT Market Data"
    build_reply = AsyncMock(return_value=reply)
    monkeypatch.setattr(crypto, "_build_market_reply", build_reply)
    with pytest.raises(MatcherFinished) as market_finished:
        await crypto.handle_market_command(
            SimpleNamespace(), SimpleNamespace(), Message(" btc ")
        )
    assert market_finished.value.message == reply
    build_reply.assert_awaited_once_with("BTCUSDT")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        ("", "用法：行情 <symbol>，例如：行情 BTC、行情 ETHUSDT"),
        ("BTC ETH", "用法：行情 <symbol>，例如：行情 BTC、行情 ETHUSDT"),
        ("USDT", "❌ symbol 格式无效，例如：BTC、ETHUSDT、SOL/USDT"),
    ],
)
async def test_handle_market_command_validates_arguments(
    finish_matchers: None, argument: str, expected: str
) -> None:
    with pytest.raises(MatcherFinished) as finished:
        await crypto.handle_market_command(
            SimpleNamespace(), SimpleNamespace(), Message(argument)
        )

    assert finished.value.message == expected


@pytest.mark.asyncio
async def test_handle_market_command_list_sends_forward_and_rejects_extra_args(
    monkeypatch: pytest.MonkeyPatch, finish_matchers: None
) -> None:
    send_list = AsyncMock(return_value=None)
    monkeypatch.setattr(crypto, "_send_market_list", send_list)
    event = fake_group_message_event_v11()
    bot = SimpleNamespace()

    with pytest.raises(MatcherFinished) as listed:
        await crypto.handle_market_command(bot, event, Message("list btc"))
    assert listed.value.message is None
    send_list.assert_awaited_once_with(bot, event, "btc")

    with pytest.raises(MatcherFinished) as usage:
        await crypto.handle_market_command(bot, event, Message("list btc usdt"))
    assert usage.value.message == "用法：/crypto list [keyword]"


@pytest.mark.asyncio
async def test_handle_market_list_and_popular_market_use_expected_symbol(
    monkeypatch: pytest.MonkeyPatch, finish_matchers: None
) -> None:
    send_list = AsyncMock(return_value="列表失败")
    monkeypatch.setattr(crypto, "_send_market_list", send_list)
    event = fake_private_message_event_v11()
    with pytest.raises(MatcherFinished) as list_finished:
        await crypto.handle_market_list(SimpleNamespace(), event, Message("eth"))
    assert list_finished.value.message == "列表失败"
    send_list.assert_awaited_once_with(SimpleNamespace(), event, "eth")

    build_reply = AsyncMock(return_value="ETH/USDT Market Data")
    monkeypatch.setattr(crypto, "_build_market_reply", build_reply)
    with pytest.raises(MatcherFinished) as popular_finished:
        await crypto.handle_popular_market(
            fake_group_message_event_v11(message=Message(" ETH "))
        )
    assert popular_finished.value.message == "ETH/USDT Market Data"
    build_reply.assert_awaited_once_with("ETHUSDT")
