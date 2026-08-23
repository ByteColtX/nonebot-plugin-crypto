"""NoneBot /crypto 命令和热门币种快捷 matcher。"""

import re

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg
from nonebot.plugin import on_regex

from .constants import (
    HELP_ARGUMENTS,
    HELP_TEXT,
    LIST_COMMAND_MAX_ARGS,
    LIST_QUERY_INDEX,
    POPULAR_PATTERN,
    POPULAR_SYMBOLS,
    SYMBOL_ALIASES,
)
from .market import build_market_reply, send_market_list
from .symbols import normalize_symbol

market_command = on_command("crypto", force_whitespace=True)
popular_market = on_regex(POPULAR_PATTERN, flags=re.IGNORECASE)


@market_command.handle()
async def handle_market_command(
    bot: Bot,
    event: GroupMessageEvent | PrivateMessageEvent,
    args: Message = CommandArg(),
) -> None:
    """处理行情查询和交易对列表命令。"""
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
        error_message = await send_market_list(bot, event, query)
        if error_message:
            await market_command.finish(error_message)
        await market_command.finish()

    if len(arguments) != 1:
        await market_command.finish(
            "用法：/crypto <symbol>，例如：/crypto BTC、/crypto ETHUSDT"
        )

    symbol = normalize_symbol(arguments[0])
    if symbol is None:
        await market_command.finish("❌ symbol 格式无效，例如：BTC、ETHUSDT、SOL/USDT")

    await market_command.finish(await build_market_reply(symbol))


@popular_market.handle()
async def handle_popular_market(
    event: GroupMessageEvent | PrivateMessageEvent,
) -> None:
    """处理静态热门币种榜单中的快捷查询。"""
    keyword = event.get_plaintext().strip().casefold()
    symbol = POPULAR_SYMBOLS.get(keyword) or SYMBOL_ALIASES.get(keyword)
    if symbol is not None:
        await popular_market.finish(await build_market_reply(symbol))
