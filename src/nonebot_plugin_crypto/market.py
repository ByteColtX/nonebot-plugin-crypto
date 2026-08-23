"""行情查询和交易对列表业务逻辑。"""

import httpx
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.exception import ActionFailed, NetworkError

from .binance import fetch_exchange_symbols, fetch_ticker_data
from .constants import HTTP_BAD_REQUEST
from .formatting import format_decimal, format_time
from .forward import send_forward_market_list
from .symbols import search_symbols, split_symbol


async def send_market_list(
    bot: Bot,
    event: GroupMessageEvent | PrivateMessageEvent,
    query: str,
) -> str | None:
    """获取、筛选并发送 Binance Spot 交易对列表。"""
    try:
        symbols = await fetch_exchange_symbols()
    except httpx.TimeoutException:
        return "❌ Binance 行情列表请求超时，请稍后再试"
    except (httpx.HTTPError, TypeError, ValueError):
        return "❌ Binance 行情列表获取失败，请稍后再试"

    matched_symbols = search_symbols(symbols, query)
    if not matched_symbols:
        return f"❌ 没有找到匹配的交易对：{query}"

    search_title = f" · Search: {query.upper()}" if query else ""
    lines = [
        f"Binance Spot Trading Pairs{search_title}",
        f"Status: TRADING | Matched: {len(matched_symbols)}",
        "",
    ]
    lines.extend(
        f"{index:04d}. {item.get('symbol', '-')}"
        for index, item in enumerate(matched_symbols, start=1)
    )

    try:
        await send_forward_market_list(bot, event, lines)
    except (ActionFailed, NetworkError):
        return "❌ 合并转发发送失败，请稍后再试"
    return None


async def build_market_reply(symbol: str) -> str:
    """获取指定交易对行情并构造用户可读的回复。"""
    try:
        data = await fetch_ticker_data(symbol)
    except httpx.TimeoutException:
        return "❌ 行情请求超时，请稍后再试"
    except httpx.HTTPStatusError as error:
        if error.response.status_code == HTTP_BAD_REQUEST:
            return f"❌ 未找到可用的 Binance 现货交易对：{symbol}"
        return f"❌ Binance 行情接口返回错误：{error.response.status_code}"
    except (httpx.HTTPError, TypeError, ValueError):
        return "❌ 行情获取失败，请稍后再试"

    base_asset, quote_asset = split_symbol(symbol)
    quote_suffix = f" {quote_asset}" if quote_asset else ""
    return "\n".join(
        [
            f"{base_asset}/{quote_asset or symbol} Market Data",
            f"Last Price: {format_decimal(data.get('lastPrice'))}{quote_suffix}",
            "24h Change: "
            f"{format_decimal(data.get('priceChange'), signed=True)}{quote_suffix} "
            f"({format_decimal(data.get('priceChangePercent'))}%)",
            f"24h High: {format_decimal(data.get('highPrice'))}{quote_suffix}",
            f"24h Low: {format_decimal(data.get('lowPrice'))}{quote_suffix}",
            f"24h Volume: {format_decimal(data.get('volume'), places=3)} {base_asset}",
            f"24h Amount: {format_decimal(data.get('quoteVolume'))}{quote_suffix}",
            f"Time: {format_time(data.get('closeTime'))} (GMT+8)",
            "Source: Binance",
        ]
    )
