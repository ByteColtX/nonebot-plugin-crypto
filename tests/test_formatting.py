import pytest

from nonebot_plugin_crypto import formatting


@pytest.mark.parametrize(
    ("value", "places", "signed", "expected"),
    [
        (None, 2, False, "-"),
        ("", 2, False, "-"),
        ("1234.5", 2, False, "1,234.50"),
        ("1.2", 2, True, "+1.20"),
        ("-1.2", 1, True, "-1.2"),
        ("unknown", 2, False, "unknown"),
    ],
)
def test_format_decimal(
    value: object, places: int, signed: bool, expected: str
) -> None:
    assert formatting.format_decimal(value, places, signed=signed) == expected


def test_format_time_converts_utc_to_shanghai_and_handles_invalid_values() -> None:
    assert formatting.format_time(0) == "1970-01-01 08:00:00"
    assert formatting.format_time("bad") == "-"
    assert formatting.format_time(None) == "-"
