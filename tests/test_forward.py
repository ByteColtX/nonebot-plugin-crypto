from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from fake import fake_group_message_event_v11, fake_private_message_event_v11
from nonebot_plugin_crypto import forward


def test_build_forward_nodes_chunks_lines_and_uses_bot_identity() -> None:
    nodes = forward.build_forward_nodes([str(index) for index in range(51)], "42")

    assert len(nodes) == 2
    assert nodes[0]["data"]["user_id"] == "42"
    assert nodes[0]["data"]["nickname"] == "Crypto Market"
    assert nodes[0]["data"]["content"][0]["data"]["text"].splitlines() == [
        str(index) for index in range(50)
    ]
    assert nodes[1]["data"]["content"][0]["data"]["text"] == "50"


@pytest.mark.asyncio
async def test_send_forward_market_list_supports_group_and_private() -> None:
    group_bot = SimpleNamespace(self_id="7", call_api=AsyncMock())
    await forward.send_forward_market_list(
        group_bot,
        fake_group_message_event_v11(group_id=42),
        ["header", "item"],
    )
    assert group_bot.call_api.await_args.args[0] == "send_group_forward_msg"
    assert group_bot.call_api.await_args.kwargs["group_id"] == 42

    private_bot = SimpleNamespace(self_id="7", call_api=AsyncMock())
    await forward.send_forward_market_list(
        private_bot,
        fake_private_message_event_v11(user_id=24),
        ["content"],
    )
    assert private_bot.call_api.await_args.args[0] == "send_private_forward_msg"
    assert private_bot.call_api.await_args.kwargs["user_id"] == 24
