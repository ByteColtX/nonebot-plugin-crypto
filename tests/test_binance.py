from unittest.mock import patch

import pytest

from nonebot_plugin_crypto import binance


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
async def test_fetch_ticker_data_sends_symbol_and_accept_header() -> None:
    response = FakeResponse({"symbol": "BTCUSDT", "lastPrice": "100"})
    client = FakeAsyncClient(response)
    with patch.object(binance.httpx, "AsyncClient", lambda **_kwargs: client):
        result = await binance.fetch_ticker_data("BTCUSDT")

    assert result["symbol"] == "BTCUSDT"
    assert client.calls == [
        (
            binance.BINANCE_TICKER_URL,
            {"symbol": "BTCUSDT"},
            {"Accept": "application/json"},
        )
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], {"symbol": "ETHUSDT"}])
async def test_fetch_ticker_data_rejects_unexpected_payload(payload: object) -> None:
    client = FakeAsyncClient(FakeResponse(payload))
    with patch.object(binance.httpx, "AsyncClient", lambda **_kwargs: client):
        with pytest.raises(TypeError):
            await binance.fetch_ticker_data("BTCUSDT")


@pytest.mark.asyncio
async def test_fetch_exchange_symbols_filters_trading_and_caches_result() -> None:
    payload = {
        "symbols": [
            {"symbol": "BTCUSDT", "status": "TRADING"},
            {"symbol": "OLDUSDT", "status": "BREAK"},
            "invalid",
        ]
    }
    client = FakeAsyncClient(FakeResponse(payload))
    with patch.object(binance.httpx, "AsyncClient", lambda **_kwargs: client):
        first = await binance.fetch_exchange_symbols()
        second = await binance.fetch_exchange_symbols()

    assert first == ({"symbol": "BTCUSDT", "status": "TRADING"},)
    assert second is first
    assert len(client.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], {"symbols": []}, {"symbols": "bad"}])
async def test_fetch_exchange_symbols_rejects_invalid_payload(payload: object) -> None:
    client = FakeAsyncClient(FakeResponse(payload))
    with patch.object(binance.httpx, "AsyncClient", lambda **_kwargs: client):
        with pytest.raises((TypeError, ValueError)):
            await binance.fetch_exchange_symbols()
