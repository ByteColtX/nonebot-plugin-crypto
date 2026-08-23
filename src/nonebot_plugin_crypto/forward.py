"""OneBot 合并转发消息工具。"""

from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from .constants import FORWARD_CHUNK_SIZE


def build_forward_nodes(lines: list[str], user_id: str) -> list[dict[str, object]]:
    """将文本行按 OneBot 合并转发限制构造成消息节点。"""
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


async def send_forward_market_list(
    bot: Bot, event: MessageEvent, lines: list[str]
) -> None:
    """根据消息类型发送交易对列表合并转发。"""
    nodes = build_forward_nodes(lines, bot.self_id)
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
