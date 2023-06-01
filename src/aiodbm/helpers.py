import asyncio
import logging
import queue
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)


class SingleWorkerThread(threading.Thread):
    """Single worker thread to run functions in parallel to an asyncio loop.

    This approach is significantly faster (approx. 1.5x) then running asyncio.to_thread(),
    which creates & destroys new threads for every function call.

    Since only a single thread is running all function calls are serialized.

    This is a daemon thread that will automatically terminate when the process exits.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        group=None,
        name=None,
        args=...,
        kwargs=None,
    ) -> None:
        super().__init__(group, None, name, args, kwargs, daemon=True)
        self._input_queue = queue.Queue()
        self._loop = loop

    async def run_soon_async(self, callable: Callable) -> Any:
        """Run a callable in the worker thread as soon as possible
        and return the result.

        If an exception occurred it will be raised.
        """
        result_queue = asyncio.Queue()
        self._input_queue.put((callable, result_queue))
        result = await result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result

    def run(self):
        """Run the scheduled functions and handle results and exceptions."""
        logger.debug("Started worker thread")
        while True:
            callable, result_queue = self._input_queue.get()
            try:
                result = callable()
            except Exception as ex:
                result = ex
            self._loop.call_soon_threadsafe(result_queue.put_nowait, result)
