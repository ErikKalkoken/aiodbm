import asyncio
import dbm
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional, Union


class DbmDatabaseAsync:
    """A DBM database."""

    def __init__(self, db, loop: asyncio.AbstractEventLoop) -> None:
        self._db = db
        self._loop = loop
        self._lock = asyncio.Lock()

    @property
    def _dbm_type_name(self) -> str:
        return type(self._db).__name__

    @property
    def is_gdbm(self) -> bool:
        return self._dbm_type_name == "gdbm"

    async def close(self) -> None:
        """Close the database."""

        def _func():
            return self._db.close()

        return await self._run_in_executor(_func)

    async def get(
        self, key: Union[str, bytes], default: Optional[bytes] = None
    ) -> Optional[bytes]:
        """Get the value of key. If the key does not exist, return default."""

        def _func():
            return self._db.get(key, default)

        return await self._run_in_executor(_func)

    async def delete(self, key: Union[str, bytes]):
        def _func():
            try:
                del self._db[key]
            except KeyError as ex:
                raise KeyError(f"Key {key} does not exist") from ex

        await self._run_in_executor(_func)

    async def exists(self, key: Union[str, bytes]) -> bool:
        """Return True when the given key exists, else False."""

        def _func():
            return key in self._db

        return await self._run_in_executor(_func)

    async def keys(self) -> List[bytes]:
        """Return existing keys."""

        def _func():
            return self._db.keys()

        return await self._run_in_executor(_func)

    async def set(self, key: Union[str, bytes], value: Union[str, bytes]) -> None:
        """Set key to hold the value.
        If key already holds a value, it is overwritten.
        """

        def _func():
            self._db[key] = value

        await self._run_in_executor(_func)

    async def setdefault(self, key: Union[str, bytes], default: bytes) -> bytes:
        """Set key to hold the default value, if it does not yet exist.
        Or return current value of existing key.
        """

        def _setdefault():
            return self._db.setdefault(key, default)

        return await self._run_in_executor(_setdefault)

    async def _run_in_executor(self, func) -> Any:
        async with self._lock:
            return await self._loop.run_in_executor(None, func)


class GdbmDatabaseAsync(DbmDatabaseAsync):
    """A GDBM database."""

    async def firstkey(self) -> bytes:
        """Return the first key for looping over all keys."""

        def _func():
            return self._db.firstkey()

        return await self._run_in_executor(_func)

    async def nextkey(self, key: Union[str, bytes]) -> Optional[bytes]:
        """Return the next key, when looping over all keys.
        Or return None, when the end of the loop has been reached.
        """

        def _func():
            return self._db.nextkey(key)

        return await self._run_in_executor(_func)

    async def reorganize(self) -> List[bytes]:
        """Reorganize the database."""

        def _func():
            return self._db.reorganize()

        return await self._run_in_executor(_func)

    async def sync(self) -> List[bytes]:
        """When the database has been opened in fast mode,
        this method forces any unwritten data to be written to the disk.
        """

        def _func():
            return self._db.sync()

        return await self._run_in_executor(_func)


@asynccontextmanager
async def open(*args, **kwargs):
    """Open the DBM database file and return a corresponding object."""

    def _open():
        return dbm.open(*args, **kwargs)

    def _close(db):
        return db.close()

    loop = asyncio.get_running_loop()
    db = await loop.run_in_executor(None, _open)

    dbm_variant = type(db).__name__
    try:
        if dbm_variant == "gdbm":
            yield GdbmDatabaseAsync(db, loop)
        else:
            yield DbmDatabaseAsync(db, loop)
    finally:
        await loop.run_in_executor(None, _close, db)


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
