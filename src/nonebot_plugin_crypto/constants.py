"""插件使用的常量。"""

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

List and search Binance Spot symbols:
/crypto list
/crypto list btc
/crypto list usdt

Options:
/crypto -h
/crypto --help"""
