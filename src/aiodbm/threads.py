import asyncio
from typing import Callable, NamedTuple, Optional


class _Message(NamedTuple):
    """A queue message."""

    future: Optional[asyncio.Future]
    func: Optional[Callable]
    is_stop_signal: bool = False

    @property
    def future_strict(self) -> asyncio.Future:
        """Return future only if it exists, else raise exception."""
        if self.future is None:
            raise ValueError("No future")
        return self.future

    @property
    def func_strict(self) -> Callable:
        """Return function only if it exists, else raise exception."""
        if self.func is None:
            raise ValueError("No func")
        return self.func

    def __str__(self) -> str:
        return str(self.func)

    @classmethod
    def create_stop_signal(cls) -> "_Message":
        return cls(None, None, is_stop_signal=True)
