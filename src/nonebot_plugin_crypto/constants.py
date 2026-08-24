"""插件使用的常量。"""

import re

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
EXCHANGE_INFO_CACHE_TTL = 300
FORWARD_CHUNK_SIZE = 50
HTTP_BAD_REQUEST = 400
HELP_ARGUMENTS = frozenset({"-h", "--help", "help"})
LIST_COMMAND_MAX_ARGS = 2
LIST_QUERY_INDEX = 1
# Binance Spot USDT 24 小时成交额 Top 20 快照，获取于 2026-08-23。
POPULAR_SYMBOLS = {
    "xrp": "XRPUSDT",
    "sol": "SOLUSDT",
    "zec": "ZECUSDT",
    "usd1": "USD1USDT",
    "trump": "TRUMPUSDT",
    "pyth": "PYTHUSDT",
    "re": "REUSDT",
    "doge": "DOGEUSDT",
    "pump": "PUMPUSDT",
    "pepe": "PEPEUSDT",
    "sui": "SUIUSDT",
    "tut": "TUTUSDT",
    "ena": "ENAUSDT",
    "link": "LINKUSDT",
    "near": "NEARUSDT",
    "ada": "ADAUSDT",
    "uni": "UNIUSDT",
    "xlm": "XLMUSDT",
    "trx": "TRXUSDT",
    "rlusd": "RLUSDUSDT",
}
SYMBOL_ALIASES = {
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
_POPULAR_PATTERN_ALTERNATIVES = sorted(
    (
        re.escape(keyword)
        for keyword in frozenset(POPULAR_SYMBOLS) | frozenset(SYMBOL_ALIASES)
    ),
    key=lambda keyword: (-len(keyword), keyword),
)
POPULAR_PATTERN = rf"^\s*(?:{'|'.join(_POPULAR_PATTERN_ALTERNATIVES)})\s*$"
HELP_TEXT = """Crypto Market Help

Query market data:
/crypto <symbol>
/crypto BTC
/crypto ETHUSDT
/crypto SOL/USDT

List and search Binance Spot symbols:
/crypto list
/crypto list btc
/crypto list usdt

Popular shortcuts:
Send one of the 20 Binance Spot USDT asset symbols from the current snapshot directly,
for example: XRP

Options:
/crypto -h
/crypto --help"""
