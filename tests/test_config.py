from nonebot_plugin_crypto.config import Config


def test_config_defaults_to_no_proxy() -> None:
    assert Config().crypto_proxy is None


def test_config_accepts_proxy_address() -> None:
    config = Config(crypto_proxy="http://127.0.0.1:7890")

    assert config.crypto_proxy == "http://127.0.0.1:7890"
