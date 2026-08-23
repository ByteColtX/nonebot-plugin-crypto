"""NoneBot /crypto 命令 matcher。"""

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import CommandArg

from .constants import (
    HELP_ARGUMENTS,
    HELP_TEXT,
    LIST_COMMAND_MAX_ARGS,
    LIST_QUERY_INDEX,
)
from .market import build_market_reply, send_market_list
from .symbols import normalize_symbol

market_command = on_command("crypto", force_whitespace=True)


@market_command.handle()
async def handle_market_command(
    bot: Bot,
    event: MessageEvent,
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
