from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from fake import fake_group_message_event_v11
from nonebot_plugin_crypto import market


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
        market, "fetch_exchange_symbols", AsyncMock(return_value=symbols)
    )
    monkeypatch.setattr(market, "send_forward_market_list", send)
    event = fake_group_message_event_v11()
    bot = SimpleNamespace(self_id="1")

    assert await market.send_market_list(bot, event, "btc") is None
    assert send.await_args.args[2] == [
        "Binance Spot Trading Pairs · Search: BTC",
        "Status: TRADING | Matched: 1",
        "",
        "0001. BTCUSDT",
    ]
    assert await market.send_market_list(bot, event, "missing") == (
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
    monkeypatch.setattr(market, "fetch_exchange_symbols", AsyncMock(side_effect=error))

    result = await market.send_market_list(
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
        market,
        "fetch_ticker_data",
        AsyncMock(return_value=make_ticker()),
    )

    result = await market.build_market_reply("BTCUSDT")

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
    monkeypatch.setattr(market, "fetch_ticker_data", AsyncMock(side_effect=error))

    assert await market.build_market_reply("BTCUSDT") == expected


@pytest.mark.asyncio
async def test_build_market_reply_maps_binance_http_status_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_request = httpx.Response(400, request=httpx.Request("GET", "https://test"))
    server_error = httpx.Response(500, request=httpx.Request("GET", "https://test"))

    monkeypatch.setattr(
        market,
        "fetch_ticker_data",
        AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "bad", request=bad_request.request, response=bad_request
            )
        ),
    )
    assert await market.build_market_reply("BTCUSDT") == (
        "❌ 未找到可用的 Binance 现货交易对：BTCUSDT"
    )

    monkeypatch.setattr(
        market,
        "fetch_ticker_data",
        AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "bad", request=server_error.request, response=server_error
            )
        ),
    )
    assert await market.build_market_reply("BTCUSDT") == (
        "❌ Binance 行情接口返回错误：500"
    )
