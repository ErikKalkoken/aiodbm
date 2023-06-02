import asyncio
import dbm
import logging
import queue
import threading
from functools import partial
from pathlib import Path
from typing import Any, Callable, Generator, List, NamedTuple, Optional, Union

logger = logging.getLogger("aiodbm")


class Message(NamedTuple):
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
    def create_stop_signal(cls) -> "Message":
        return cls(None, None, is_stop_signal=True)


class DbmDatabase(threading.Thread):
    """A proxy for a DBM database."""

    def __init__(self, connector: Callable) -> None:
        super().__init__()
        self._database = None
        self._connector = connector
        self._message_queue = queue.Queue()

    def __await__(self) -> Generator[Any, None, "DbmDatabase"]:
        return self._connect().__await__()

    async def __aenter__(self) -> "DbmDatabase":
        return await self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def _db(self):
        """Return current database if one exists, else raise exception."""
        if self._database is None:
            raise ValueError("no active database")

        return self._database

    @property
    def _dbm_type_name(self) -> str:
        return type(self._db).__name__

    @property
    def is_gdbm(self) -> bool:
        """Return True if this is a GDBM database."""
        return self._dbm_type_name == "gdbm"

    async def _connect(self) -> "DbmDatabase":
        """Connect to the actual DBM database."""
        if self._database is not None:
            raise RuntimeError("Already connected")

        self.start()
        try:
            future = asyncio.get_running_loop().create_future()
            self._message_queue.put_nowait(Message(future, self._connector))
            self._database = await future
        except Exception:
            self._database = None
            self._stop_runner()
            raise

        return self

    def run(self) -> None:
        """
        Execute function calls on a separate thread.

        :meta private:
        """

        while True:  # Continues running until stop signal is received
            message: Message = self._message_queue.get()
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

    def _stop_runner(self):
        """Stop the thread runner."""
        stop_signal = Message.create_stop_signal()
        self._message_queue.put_nowait(stop_signal)

    async def _execute(self, fn, *args, **kwargs):
        """Queue a function with the given arguments for execution in the runner."""
        if self._database is None:
            raise ValueError("Database closed")

        func = partial(fn, *args, **kwargs)
        future = asyncio.get_running_loop().create_future()

        self._message_queue.put_nowait(Message(future, func))

        return await future

    # DBM API

    async def close(self) -> None:
        """Complete queued operations and close the database."""

        if self._database is None:
            self._stop_runner()
            return

        try:
            await self._execute(self._db.close)
        except Exception:
            logger.warning("exception occurred while closing database")
            raise
        finally:
            self._database = None
            self._stop_runner()

    async def delete(self, key: Union[str, bytes]):
        """Delete given key."""

        def _func():
            try:
                del self._db[key]
            except KeyError as ex:
                raise KeyError(f"Key {key} does not exist") from ex

        return await self._execute(_func)

    async def exists(self, key: Union[str, bytes]) -> bool:
        """Return True when the given key exists, else False."""

        def _func():
            return key in self._db

        return await self._execute(_func)

    async def get(
        self, key: Union[str, bytes], default: Optional[bytes] = None
    ) -> Optional[bytes]:
        """Get the value of key. If the key does not exist, return default."""

        return await self._execute(self._db.get, key, default)

    async def keys(self) -> List[bytes]:
        """Return existing keys."""

        return await self._execute(self._db.keys)

    async def set(self, key: Union[str, bytes], value: Union[str, bytes]) -> None:
        """Set key to hold the value.
        If key already holds a value, it is overwritten.
        """

        def _set():
            self._db[key] = value

        await self._execute(_set)

    async def setdefault(self, key: Union[str, bytes], default: bytes) -> bytes:
        """Set key to hold the default value, if it does not yet exist.
        Or return current value of existing key.
        """

        return await self._execute(self._db.setdefault, key, default)

    # GDBM only API

    async def firstkey(self) -> bytes:
        """Return the first key for looping over all keys."""

        return await self._execute(self._db.firstkey)

    async def nextkey(self, key: Union[str, bytes]) -> Optional[bytes]:
        """Return the next key, when looping over all keys.
        Or return None, when the end of the loop has been reached.
        """

        return await self._execute(self._db.nextkey, key)

    async def reorganize(self) -> None:
        """Reorganize the database."""

        await self._execute(self._db.reorganize)

    async def sync(self) -> None:
        """When the database has been opened in fast mode,
        this method forces any unwritten data to be written to the disk.
        """

        await self._execute(self._db.sync)


def open(file: Union[str, Path], *args, **kwargs) -> DbmDatabase:
    """Create and return a proxy to the DBM database.

    Example:

    .. code-block:: Python

    async with open("example.dbm", "c") as db:
        ...

    Args:
        file: filename for the DBM database

    Returns:
        DBM database proxy object
    """

    def connector():
        filepath = str(file)
        return dbm.open(filepath, *args, **kwargs)

    return DbmDatabase(connector)


async def whichdb(filename: Union[str, Path]) -> Optional[str]:
    """Return the name of the DBM implementation,
    which can be used for opening the given file.

    Or if the file can not be read return None.
    Or if the file is not in a known DBM format, return an empty string.
    """

    def _func():
        return dbm.whichdb(str(filename))

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _func)
