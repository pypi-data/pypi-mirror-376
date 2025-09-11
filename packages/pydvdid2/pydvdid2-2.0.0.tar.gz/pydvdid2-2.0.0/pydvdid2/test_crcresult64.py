"""Implements tests for the pydvdid.crc64result module.
"""


from pydvdid.crc64result import Crc64Result


def test_crc64result_high_bytes_returns_correct_value() -> None:
    result = Crc64Result(2246800662182009355)
    assert("1f2e3d4c" == result.high_bytes)


def crc64result_low_bytes_returns_correct_value() -> None:
    result = Crc64Result(2246800662182009355)
    assert("56789a0b" == result.low_bytes)


def test_crc64result_equality() -> None:
    assert(Crc64Result(1) == Crc64Result(1))
    assert(Crc64Result(2) == Crc64Result(2))
    assert(Crc64Result(2246800662182009355) == Crc64Result(2246800662182009355))
    assert(Crc64Result(1) != Crc64Result(2))
    assert(Crc64Result(2) != Crc64Result(1))
    assert(Crc64Result(2246800662182009355) != Crc64Result(1))


def test_crc64result___str___() -> None:
    result = Crc64Result(2246800662182009355)
    assert(str(result) == "1f2e3d4c56789a0b")

