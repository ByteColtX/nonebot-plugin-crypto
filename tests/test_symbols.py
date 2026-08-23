import pytest

from nonebot_plugin_crypto import symbols


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
    assert symbols.normalize_symbol(value) == expected


def test_split_symbol_prefers_longest_quote_asset() -> None:
    assert symbols.split_symbol("BTCUSDT") == ("BTC", "USDT")
    assert symbols.split_symbol("ETHBTC") == ("ETH", "BTC")
    assert symbols.split_symbol("UNKNOWN") == ("UNKNOWN", "")


def test_search_symbols_matches_symbol_base_quote_and_alias() -> None:
    records = (
        {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT"},
        {"symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC"},
        {"symbol": "SOLUSDC", "baseAsset": "SOL", "quoteAsset": "USDC"},
    )

    assert len(symbols.search_symbols(records, "btc")) == 2
    assert symbols.search_symbols(records, "sol/usdc") == (records[2],)
    assert len(symbols.search_symbols(records, "usdt")) == 1
    assert symbols.search_symbols(records, "missing") == ()
    assert symbols.search_symbols(records, "") == records
