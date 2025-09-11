"""Implements package-level import control.
"""


from .exceptions import (
    FileContentReadException,
    FileTimeOutOfRangeException,
    PathDoesNotExistException,
    PydvdidException
)
from .functions import compute


__all__ = [
    "main",
    "compute",
    "FileContentReadException",
    "FileTimeOutOfRangeException",
    "PathDoesNotExistException",
    "PydvdidException"
]

def main():

    import sys

    if len(sys.argv) == 2:
        print(compute(sys.argv[1]))
        sys.exit(0)

    print("Usage: pydvdid <path>")
    sys.exit(1)
