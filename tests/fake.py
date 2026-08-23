from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import (
        GroupMessageEvent as GroupMessageEventV11,
    )
    from nonebot.adapters.onebot.v11 import (
        PrivateMessageEvent as PrivateMessageEventV11,
    )


def fake_group_message_event_v11(**fields: object) -> "GroupMessageEventV11":
    """创建用于调用 handler 的最小 OneBot 群消息事件。"""
    import random

    from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
    from nonebot.adapters.onebot.v11.event import Reply, Sender
    from pydantic import create_model

    fake_event = create_model("FakeGroupMessageEvent", __base__=GroupMessageEvent)

    class Event(fake_event):
        time: int = 1_000_000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "normal"
        user_id: int = 12345678
        message_type: Literal["group"] = "group"
        group_id: int = 87654321
        message_id: int = random.randint(1, 10_000_000)
        message: Message = Message("test")
        original_message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(card="", nickname="test", role="member")
        to_me: bool = False
        reply: Reply | None = None

    return Event(**fields)


def fake_private_message_event_v11(**fields: object) -> "PrivateMessageEventV11":
    """创建用于调用 handler 的最小 OneBot 私聊消息事件。"""
    from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent
    from nonebot.adapters.onebot.v11.event import Sender
    from pydantic import create_model

    fake_event = create_model("FakePrivateMessageEvent", __base__=PrivateMessageEvent)

    class Event(fake_event):
        time: int = 1_000_000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "friend"
        user_id: int = 10
        message_type: Literal["private"] = "private"
        message_id: int = 1
        message: Message = Message("test")
        original_message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(nickname="test")
        to_me: bool = False

    return Event(**fields)
