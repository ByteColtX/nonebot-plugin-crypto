"""NoneBot 加密货币行情插件。"""

from nonebot.plugin import PluginMetadata

from . import handlers as _handlers  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="加密货币行情",
    description="基于 Binance Public API 的加密货币实时行情和交易对列表插件。",
    usage="/crypto <symbol> 查询实时行情；/crypto list [keyword] 查询交易对列表。",
    type="application",
    homepage="https://github.com/ByteColtX/nonebot-plugin-crypto",
    supported_adapters={"~onebot.v11"},
)
