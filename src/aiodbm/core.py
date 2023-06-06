"""Core logic for an async DBM proxy."""

import asyncio
import dbm
import logging
from dbm import error
from functools import partial
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Generator, List, Optional, Union

from aiodbm.threads import ThreadRunner

logger = logging.getLogger("aiodbm")


__all__ = ["Database", "error", "open", "whichdb"]


class Database:
    """A DBM database.

    Not that some methods are available on GDBM only.
    You can check if your database is GDBM with :func:`is_gdbm`.
    """

    def __init__(self, connector: Callable) -> None:
        super().__init__()
        self._db = None
        self._connector = connector
        self._runner = ThreadRunner()

    def __await__(self) -> Generator[Any, None, "Database"]:
        return self._connect().__await__()

    async def __aenter__(self) -> "Database":
        return await self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def _db_strict(self):
        """Return current database if one is active, else raise exception."""
        if self._db is None:
            raise ValueError("no active database")

        return self._db

    @property
    def _dbm_type_name(self) -> str:
        """Return name of the currently active DBM variant."""
        return type(self._db_strict).__name__

    @property
    def is_gdbm(self) -> bool:
        """Return True if this is a GDBM database."""
        return self._dbm_type_name == "gdbm"

    async def _connect(self) -> "Database":
        """Connect to the actual DBM database."""
        if self._db is not None:
            raise RuntimeError("Already connected")

        self._runner.start()
        try:
            self._db = await self._runner.call_soon(self._connector)
        except Exception:
            self._db = None
            self._runner.stop()
            raise

        return self

    async def _execute(self, fn, *args, **kwargs) -> Any:
        """Queue a function with the given arguments for execution in the runner."""
        if self._db is None:
            raise ValueError("Database closed")

        func = partial(fn, *args, **kwargs)
        return await self._runner.call_soon(func)

    # DBM API

    async def close(self) -> None:
        """Complete queued operations and close the database."""

        if self._db is None:
            return

        try:
            await self._execute(self._db_strict.close)
        except Exception:
            logger.warning("exception occurred while closing database")
            raise
        finally:
            self._db = None
            self._runner.stop()

    async def delete(self, key: Union[str, bytes]) -> None:
        """Delete given key."""

        def _func():
            try:
                del self._db_strict[key]
            except KeyError as ex:
                raise KeyError(f"Key {key} does not exist") from ex

        return await self._execute(_func)

    async def exists(self, key: Union[str, bytes]) -> bool:
        """Return True when the given key exists, else False."""

        def _func():
            return key in self._db_strict

        return await self._execute(_func)

    async def get(
        self, key: Union[str, bytes], default: Optional[bytes] = None
    ) -> Optional[bytes]:
        """Get the value of key. If the key does not exist, return default."""

        return await self._execute(self._db_strict.get, key, default)

    async def keys(self) -> List[bytes]:
        """Return existing keys."""

        return await self._execute(self._db_strict.keys)

    async def set(self, key: Union[str, bytes], value: Union[str, bytes]) -> None:
        """Set key to hold the value.
        If key already holds a value, it is overwritten.
        """

        def _set():
            self._db_strict[key] = value

        await self._execute(_set)

    async def setdefault(self, key: Union[str, bytes], default: bytes) -> bytes:
        """Set key to hold the default value, if it does not yet exist.
        Or return current value of existing key.
        """

        return await self._execute(self._db_strict.setdefault, key, default)

    # GDBM only API

    async def firstkey(self) -> bytes:
        """Return the first key for looping over all keys. GDBM only."""

        return await self._execute(self._db_strict.firstkey)

    async def keys_iterator(self) -> AsyncGenerator[bytes, None]:
        """Return all keys as async generator. GDBM only.

        In contrast to :func:`keys` this method will not load the full list of keys into
        memory, but instead fetch keys one after the other.

        Note that the order of keys is implementation specific
        and can not be relied on.

        Usage example:

        .. code-block:: Python

            async for key in db.keys_iterator():
                print(key)

        """
        key = await self.firstkey()
        while key is not None:
            yield key
            key = await self.nextkey(key)

    async def nextkey(self, key: Union[str, bytes]) -> Optional[bytes]:
        """Return the next key, when looping over all keys.
        Or return None, when the end of the loop has been reached.
        GDBM only.
        """

        return await self._execute(self._db_strict.nextkey, key)

    async def reorganize(self) -> None:
        """Reorganize the database. GDBM only."""

        await self._execute(self._db_strict.reorganize)

    async def sync(self) -> None:
        """When the database has been opened in fast mode,
        this method forces any unwritten data to be written to the disk.
        GDBM only.
        """

        await self._execute(self._db_strict.sync)


def open(file: Union[str, Path], *args, **kwargs) -> Database:
    """Create and return a proxy to a DBM database.

    Args:
        file: filename for the DBM database

    Returns:
        DBM database proxy object

    Usage A:

    .. code-block:: Python

        async with open("example.dbm", "c") as db:
            ...

    Usage B:

    .. code-block:: Python

        db = async open("example.dbm", "c"):
        ...
        await db.close()
    """

    def connector():
        filepath = str(file)
        return dbm.open(filepath, *args, **kwargs)

    return Database(connector)


async def whichdb(filename: Union[str, Path]) -> Optional[str]:
    """Return the name of the DBM implementation,
    which can be used for opening the given file.

    Or if the file can not be read return None.
    Or if the file is not in a known DBM format, return an empty string.
    """

    filename_str = str(filename)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, dbm.whichdb, filename_str)
