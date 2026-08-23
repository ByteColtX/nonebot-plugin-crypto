import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, DecimalException
from time import monotonic
from zoneinfo import ZoneInfo

import httpx
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed, NetworkError
from nonebot.params import CommandArg
from nonebot.plugin import on_regex

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
EXCHANGE_INFO_CACHE_TTL = 300
FORWARD_CHUNK_SIZE = 50
HTTP_BAD_REQUEST = 400
HELP_ARGUMENTS = frozenset({"-h", "--help", "help"})
LIST_COMMAND_MAX_ARGS = 2
LIST_QUERY_INDEX = 1
POPULAR_SYMBOLS = {
    "btc": "BTCUSDT",
    "bitcoin": "BTCUSDT",
    "eth": "ETHUSDT",
    "ethereum": "ETHUSDT",
    "bnb": "BNBUSDT",
    "sol": "SOLUSDT",
    "solana": "SOLUSDT",
    "doge": "DOGEUSDT",
    "dogecoin": "DOGEUSDT",
    "xrp": "XRPUSDT",
}
POPULAR_PATTERN = (
    r"^\s*(?:btc|bitcoin|eth|ethereum|bnb|sol|solana|"
    r"doge|dogecoin|xrp)\s*$"
)
QUOTE_ASSETS = (
    "USDT",
    "USDC",
    "FDUSD",
    "TUSD",
    "BUSD",
    "BTC",
    "ETH",
    "BNB",
    "EUR",
    "TRY",
    "BRL",
    "AUD",
    "GBP",
    "RUB",
    "ZAR",
    "UAH",
    "NGN",
    "IDRT",
    "PLN",
    "RON",
    "ARS",
    "MXN",
    "COP",
    "PEN",
    "JPY",
    "KRW",
    "VND",
    "DAI",
)
HELP_TEXT = """Crypto Market Help

Query market data:
/crypto <symbol>
/crypto BTC
/crypto ETHUSDT
/crypto SOL/USDT

Aliases:
/行情 <symbol>   /price <symbol>   /market <symbol>

List and search Binance Spot symbols:
/crypto list
/crypto list btc
/crypto list usdt

Legacy alias:
/行情列表 [keyword]

Popular keywords:
btc · eth · bnb · sol · doge · xrp

Options:
/crypto -h
/crypto --help"""


@dataclass(slots=True)
class _ExchangeInfoCache:
    expires_at: float = 0
    symbols: tuple[Mapping[str, object], ...] = ()


_exchange_info_cache = _ExchangeInfoCache()

market_command = on_command(
    "行情",
    aliases={"price", "crypto", "market", "币价"},
    force_whitespace=True,
)
market_list_command = on_command(
    "行情列表",
    aliases={"symbols", "symbol", "交易对", "币种列表"},
)
popular_market = on_regex(POPULAR_PATTERN, flags=re.IGNORECASE)


def _format_decimal(value: object, places: int = 2, *, signed: bool = False) -> str:
    if value is None or value == "":
        return "-"

    try:
        number = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        return str(value)

    result = f"{number:,.{places}f}"
    if signed and number > 0:
        return f"+{result}"
    return result


def _format_time(value: object) -> str:
    try:
        timestamp = int(str(value)) / 1000
        date_time = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
        return date_time.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (TypeError, ValueError, OSError):
        return "-"


def _normalize_symbol(value: str) -> str | None:
    normalized = value.strip().upper().replace("/", "").replace("-", "")
    popular_symbol = POPULAR_SYMBOLS.get(normalized.casefold())
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


def _split_symbol(symbol: str) -> tuple[str, str]:
    for quote_asset in sorted(QUOTE_ASSETS, key=len, reverse=True):
        if symbol.endswith(quote_asset) and len(symbol) > len(quote_asset):
            return symbol[: -len(quote_asset)], quote_asset
    return symbol, ""


async def _fetch_ticker_data(symbol: str) -> Mapping[str, object]:
    async with httpx.AsyncClient(timeout=10) as client:
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


async def _fetch_exchange_symbols() -> tuple[Mapping[str, object], ...]:
    now = monotonic()
    if _exchange_info_cache.expires_at > now:
        return _exchange_info_cache.symbols

    async with httpx.AsyncClient(timeout=20) as client:
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


def _search_symbols(
    symbols: tuple[Mapping[str, object], ...], query: str
) -> tuple[Mapping[str, object], ...]:
    normalized_query = query.strip().upper().replace("/", "").replace("-", "")
    popular_symbol = POPULAR_SYMBOLS.get(normalized_query.casefold())
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


def _build_forward_nodes(lines: list[str], user_id: str) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    for index in range(0, len(lines), FORWARD_CHUNK_SIZE):
        content = "\n".join(lines[index : index + FORWARD_CHUNK_SIZE])
        nodes.append(
            {
                "type": "node",
                "data": {
                    "user_id": user_id,
                    "nickname": "Crypto Market",
                    "content": [
                        {"type": "text", "data": {"text": content}},
                    ],
                },
            }
        )
    return nodes


async def _send_forward_market_list(
    bot: Bot, event: MessageEvent, lines: list[str]
) -> None:
    nodes = _build_forward_nodes(lines, bot.self_id)
    if event.message_type == "group":
        await bot.call_api(
            "send_group_forward_msg",
            group_id=event.group_id,
            messages=nodes,
        )
    else:
        await bot.call_api(
            "send_private_forward_msg",
            user_id=event.user_id,
            messages=nodes,
        )


async def _send_market_list(bot: Bot, event: MessageEvent, query: str) -> str | None:
    try:
        symbols = await _fetch_exchange_symbols()
    except httpx.TimeoutException:
        return "❌ Binance 行情列表请求超时，请稍后再试"
    except (httpx.HTTPError, TypeError, ValueError):
        return "❌ Binance 行情列表获取失败，请稍后再试"

    matched_symbols = _search_symbols(symbols, query)
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
        await _send_forward_market_list(bot, event, lines)
    except (ActionFailed, NetworkError):
        return "❌ 合并转发发送失败，请稍后再试"
    return None


async def _build_market_reply(symbol: str) -> str:
    try:
        data = await _fetch_ticker_data(symbol)
    except httpx.TimeoutException:
        return "❌ 行情请求超时，请稍后再试"
    except httpx.HTTPStatusError as error:
        if error.response.status_code == HTTP_BAD_REQUEST:
            return f"❌ 未找到可用的 Binance 现货交易对：{symbol}"
        return f"❌ Binance 行情接口返回错误：{error.response.status_code}"
    except (httpx.HTTPError, TypeError, ValueError):
        return "❌ 行情获取失败，请稍后再试"

    base_asset, quote_asset = _split_symbol(symbol)
    quote_suffix = f" {quote_asset}" if quote_asset else ""
    return "\n".join(
        [
            f"{base_asset}/{quote_asset or symbol} Market Data",
            f"Last Price: {_format_decimal(data.get('lastPrice'))}{quote_suffix}",
            "24h Change: "
            f"{_format_decimal(data.get('priceChange'), signed=True)}{quote_suffix} "
            f"({_format_decimal(data.get('priceChangePercent'))}%)",
            f"24h High: {_format_decimal(data.get('highPrice'))}{quote_suffix}",
            f"24h Low: {_format_decimal(data.get('lowPrice'))}{quote_suffix}",
            f"24h Volume: {_format_decimal(data.get('volume'), places=3)} {base_asset}",
            f"24h Amount: {_format_decimal(data.get('quoteVolume'))}{quote_suffix}",
            f"Time: {_format_time(data.get('closeTime'))} (GMT+8)",
            "Source: Binance",
        ]
    )


@market_command.handle()
async def handle_market_command(
    bot: Bot,
    event: MessageEvent,
    args: Message = CommandArg(),
) -> None:
    argument_text = args.extract_plain_text().strip()
    if argument_text.casefold() in HELP_ARGUMENTS:
        await market_command.finish(HELP_TEXT)

    arguments = argument_text.split()
    if arguments and arguments[0].casefold() in {"list", "ls"}:
        if len(arguments) > LIST_COMMAND_MAX_ARGS:
            await market_command.finish("用法：/crypto list [keyword]")
        if (
            len(arguments) == LIST_COMMAND_MAX_ARGS
            and arguments[LIST_QUERY_INDEX].casefold() in HELP_ARGUMENTS
        ):
            await market_command.finish(HELP_TEXT)
        query = (
            arguments[LIST_QUERY_INDEX]
            if len(arguments) == LIST_COMMAND_MAX_ARGS
            else ""
        )
        error_message = await _send_market_list(bot, event, query)
        if error_message:
            await market_command.finish(error_message)
        await market_command.finish()

    if len(arguments) != 1:
        await market_command.finish("用法：行情 <symbol>，例如：行情 BTC、行情 ETHUSDT")

    symbol = _normalize_symbol(arguments[0])
    if symbol is None:
        await market_command.finish("❌ symbol 格式无效，例如：BTC、ETHUSDT、SOL/USDT")

    await market_command.finish(await _build_market_reply(symbol))


@market_list_command.handle()
async def handle_market_list(
    bot: Bot,
    event: MessageEvent,
    args: Message = CommandArg(),
) -> None:
    query = args.extract_plain_text().strip()
    error_message = await _send_market_list(bot, event, query)
    if error_message:
        await market_list_command.finish(error_message)
    await market_list_command.finish()


@popular_market.handle()
async def handle_popular_market(event: MessageEvent) -> None:
    keyword = event.get_plaintext().strip().casefold()
    symbol = POPULAR_SYMBOLS[keyword]
    await popular_market.finish(await _build_market_reply(symbol))
