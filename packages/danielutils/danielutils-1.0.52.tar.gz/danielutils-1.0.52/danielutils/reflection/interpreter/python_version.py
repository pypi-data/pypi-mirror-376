import platform


def _get_python_version_untyped() -> tuple:
    values = (int(v) for v in platform.python_version().split("."))
    return tuple(values)  # type:ignore


if _get_python_version_untyped() < (3, 9):
    from typing import Tuple as Tuple
else:
    from builtins import tuple as Tuple  # type:ignore


def get_python_version() -> Tuple[int, int, int]:
    """return the version of python that is currently running this code

    Returns:
        tuple[int, int, int]: version
    """
    return _get_python_version_untyped()  # type:ignore


__all__ = [
    "get_python_version"
]
