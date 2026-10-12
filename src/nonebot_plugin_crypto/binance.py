"""Binance Public API 客户端。"""

from collections.abc import Mapping
from dataclasses import dataclass
from time import monotonic

import httpx
from nonebot import get_plugin_config

from .config import Config
from .constants import (
    BINANCE_EXCHANGE_INFO_URL,
    BINANCE_TICKER_URL,
    EXCHANGE_INFO_CACHE_TTL,
)

plugin_config = get_plugin_config(Config)


def create_client(timeout: int) -> httpx.AsyncClient:
    """创建应用了插件代理配置的 httpx 异步客户端。

    Args:
        timeout: 请求超时时间，单位为秒。

    Returns:
        配置了超时时间和可选代理的异步 HTTP 客户端。
    """
    return httpx.AsyncClient(
        timeout=timeout,
        proxy=plugin_config.crypto_proxy or None,
    )


@dataclass(slots=True)
class _ExchangeInfoCache:
    expires_at: float = 0
    symbols: tuple[Mapping[str, object], ...] = ()


_exchange_info_cache = _ExchangeInfoCache()


async def fetch_ticker_data(symbol: str) -> Mapping[str, object]:
    """获取指定 Binance 交易对的 24 小时行情。"""
    async with create_client(timeout=10) as client:
        response = await client.get(
            BINANCE_TICKER_URL,
            params={"symbol": symbol},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict) or payload.get("symbol") != symbol:
        raise TypeError
    return payload


async def fetch_exchange_symbols() -> tuple[Mapping[str, object], ...]:
    """获取并缓存 Binance Spot 中处于交易状态的交易对。"""
    now = monotonic()
    if _exchange_info_cache.expires_at > now:
        return _exchange_info_cache.symbols

    async with create_client(timeout=20) as client:
        response = await client.get(
            BINANCE_EXCHANGE_INFO_URL,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise TypeError
    records = payload.get("symbols")
    if not isinstance(records, list):
        raise TypeError

    symbols = tuple(
        item
        for item in records
        if isinstance(item, dict) and item.get("status") == "TRADING"
    )
    if not symbols:
        raise ValueError

    _exchange_info_cache.symbols = symbols
    _exchange_info_cache.expires_at = now + EXCHANGE_INFO_CACHE_TTL
    return symbols
