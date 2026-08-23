"""Binance 交易对处理工具。"""

import re
from collections.abc import Mapping

from .constants import QUOTE_ASSETS, SYMBOL_ALIASES


def normalize_symbol(value: str) -> str | None:
    """将用户输入规范化为 Binance 交易对。"""
    normalized = value.strip().upper().replace("/", "").replace("-", "")
    popular_symbol = SYMBOL_ALIASES.get(normalized.casefold())
    if popular_symbol:
        return popular_symbol
    if normalized in QUOTE_ASSETS:
        return None
    if any(
        normalized.endswith(quote_asset) and len(normalized) > len(quote_asset)
        for quote_asset in QUOTE_ASSETS
    ):
        return normalized
    if re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", normalized):
        return f"{normalized}USDT"
    return None


def split_symbol(symbol: str) -> tuple[str, str]:
    """将交易对拆分为基础资产和报价资产。"""
    for quote_asset in sorted(QUOTE_ASSETS, key=len, reverse=True):
        if symbol.endswith(quote_asset) and len(symbol) > len(quote_asset):
            return symbol[: -len(quote_asset)], quote_asset
    return symbol, ""


def search_symbols(
    symbols: tuple[Mapping[str, object], ...], query: str
) -> tuple[Mapping[str, object], ...]:
    """按交易对、基础资产或报价资产搜索交易对。"""
    normalized_query = query.strip().upper().replace("/", "").replace("-", "")
    popular_symbol = SYMBOL_ALIASES.get(normalized_query.casefold())
    if popular_symbol:
        normalized_query = popular_symbol.removesuffix("USDT")

    if not normalized_query:
        return symbols

    return tuple(
        item
        for item in symbols
        if normalized_query in str(item.get("symbol", "")).upper()
        or normalized_query in str(item.get("baseAsset", "")).upper()
        or normalized_query in str(item.get("quoteAsset", "")).upper()
    )
