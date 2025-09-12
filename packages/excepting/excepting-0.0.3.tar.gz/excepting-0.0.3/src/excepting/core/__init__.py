from contextlib import contextmanager
from typing import *

__all__ = ["Exceptor"]


class Exceptor:

    "This class captures exceptions."

    __slots__ = ("_captured",)

    captured: Optional[BaseException]

    def __init__(self: Self) -> None:
        "This magic method initializes the current instance."
        self._captured = None

    @contextmanager
    def capture(self: Self, *args: type[BaseException]) -> Generator[Self, None, None]:
        "This contextmanager captures exceptions."
        self._captured = None
        exc: BaseException
        try:
            yield self
        except args as exc:
            self._captured = exc

    @property
    def captured(self: Self) -> Optional[BaseException]:
        "This property stores the captured exception."
        return self._captured
