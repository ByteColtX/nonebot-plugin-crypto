import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from pytest_asyncio import is_async_test

nonebot.init()

from nonebot_plugin_crypto import binance


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


@pytest.fixture(autouse=True)
def reset_exchange_info_cache() -> None:
    """避免交易对缓存污染不同测试。"""
    binance._exchange_info_cache.expires_at = 0
    binance._exchange_info_cache.symbols = ()
