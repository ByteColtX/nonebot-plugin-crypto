import sys
from pathlib import Path

import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from pytest_asyncio import is_async_test

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

nonebot.init()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
def initialize_nonebot() -> None:
    """为直接调用 matcher handler 的测试注册 OneBot 适配器。"""
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)
