import asyncio
import logging
import queue
import threading
from typing import Callable, NamedTuple, Optional

logger = logging.getLogger("aiodbm")


class ThreadRunner(threading.Thread):
    """A thread for running functions."""

    def __init__(self):
        super().__init__()
        self._message_queue = queue.Queue()

    def call_soon(self, future: asyncio.Future, func: Callable):
        """Schedule this function to be called soon
        and return the result in the future.

        The future will wait for the thread to start if it not yet running.
        """
        if not self.is_alive():
            raise RuntimeError("Thread is not running.")
        self._message_queue.put_nowait(_Message(future, func))

    def run(self) -> None:
        """
        Execute function calls on a separate thread.
        :meta private:
        """

        while True:  # Continues running until stop signal is received
            message: _Message = self._message_queue.get()
            if message.is_stop_signal:
                break

            logger.debug("executing %s", message)
            try:
                result = message.func_strict()
            except BaseException as ex:
                logger.debug("returning exception %s", ex)

                def set_exception(fut, e):
                    if not fut.done():
                        fut.set_exception(e)

                message.future_strict.get_loop().call_soon_threadsafe(
                    set_exception, message.future_strict, ex
                )
            else:
                logger.debug("operation %s completed", message)

                def set_result(fut, result):
                    if not fut.done():
                        fut.set_result(result)

                message.future_strict.get_loop().call_soon_threadsafe(
                    set_result, message.future_strict, result
                )

    def stop(self):
        """Stop the thread runner."""
        stop_signal = _Message.create_stop_signal()
        self._message_queue.put_nowait(stop_signal)


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
