"""插件配置项。"""

from pydantic import BaseModel


class Config(BaseModel):
    """nonebot-plugin-crypto 的插件配置。

    Attributes:
        crypto_proxy: 访问 Binance API 时使用的代理地址，例如
            ``http://127.0.0.1:7890``；留空时不使用代理。
    """

    crypto_proxy: str | None = None
