import asyncio
import logging
import queue
import threading
import weakref
from typing import Any, Callable, NamedTuple, Optional

logger = logging.getLogger(__name__)


class Message(NamedTuple):
    """Message to communicate between coroutine and thread worker."""

    callable: Optional[Callable]
    result_queue: Optional[asyncio.Queue]
    is_stop_signal: bool = False

    def callable_safe(self) -> Callable:
        """Return a callable or raise exception."""
        if not self.callable:
            raise ValueError("No callable")
        return self.callable

    def _result_queue_safe(self) -> asyncio.Queue:
        """Return return queue or raise exception."""
        if not self.result_queue:
            raise ValueError("No result queue")
        return self.result_queue

    async def wait_for_result(self) -> Any:
        """Coroutine to wait for result from other thread.
        Reraise exception here if any occurred.
        """
        result = await self._result_queue_safe().get()
        if isinstance(result, Exception):
            raise result
        return result

    def send_result(self, result: Any, loop: asyncio.AbstractEventLoop):
        """Send back the results from other thread to waiting coroutine."""
        loop.call_soon_threadsafe(self._result_queue_safe().put_nowait, result)

    @classmethod
    def create(cls, callable: Callable) -> "Message":
        """Create new object from a callable."""
        return cls(callable=callable, result_queue=asyncio.Queue())

    @classmethod
    def create_stop_signal(cls) -> "Message":
        """Create a stop signal."""
        return cls(callable=None, result_queue=None, is_stop_signal=True)


class ThreadRunner(threading.Thread):
    """A runner for executing a callable in a single running thread from a coroutine.

    This approach has significantly better throughput (approx. 1.5x)
    then the asyncio.to_thread(),
    which presumably starts and destroys new threads for every call.

    Since only a single thread is running all function calls are always serialized.

    A started thread must be stopped later or it will block a program from exiting.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        group=None,
        name=None,
        args=...,
        kwargs=None,
    ) -> None:
        super().__init__(group, None, name, args, kwargs)
        self._input_queue = queue.Queue()
        self._loop = loop
        self._finalizer = weakref.finalize(self, self.stop)

    async def run_soon_async(self, callable: Callable) -> Any:
        """Run a callable in the worker thread as soon as possible
        and return the result.

        If an exception occurred it will be raised.
        """
        message = Message.create(callable)
        self._input_queue.put(message)
        result = await message.wait_for_result()
        return result

    def run(self):
        """Run the callable and send back results and exceptions."""
        logger.debug("Started worker thread")
        while True:
            message: Message = self._input_queue.get()
            if message.is_stop_signal:
                break
            try:
                result = message.callable_safe()()
            except Exception as ex:
                result = ex
            message.send_result(result, self._loop)

    def stop(self):
        """Send stop signal to runner."""
        if self.is_alive():
            stop_signal = Message.create_stop_signal()
            self._input_queue.put_nowait(stop_signal)
