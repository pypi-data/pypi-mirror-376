"""Implements the Crc64Result class.
"""


class Crc64Result:
    """Implements a class that represents the result of a 64-bit Cyclic Redundancy Check checksum.
    """

    def __init__(self, crc64: int):
        self._crc64 = crc64


    @property
    def high_bytes(self) -> str:
        """Returns the topmost 4 bytes of the checksum formatted as a lowercase hex string.
        """

        return format(self._crc64 >> 32, "08x")


    @property
    def low_bytes(self) -> str:
        """Returns the bottommost 4 bytes of the checksum formatted as a lowercase hex string.
        """

        return format(self._crc64 & 0xffffffff, "08x")


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Crc64Result):
            return False
        return self._crc64 == other._crc64 # pylint: disable=locally-disabled, protected-access


    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


    def __str__(self) -> str:
        return format(self._crc64, "016x")
