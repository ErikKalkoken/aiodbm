import asyncio
import dbm
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional, Union


class _DatabaseAsync:
    """A DBM database."""

    def __init__(self, db, loop: asyncio.AbstractEventLoop) -> None:
        self._db = db
        self._loop = loop
        self._lock = asyncio.Lock()

    async def get(self, key: Union[str, bytes]) -> Optional[bytes]:
        """Get the value of key. If the key does not exist, return None."""

        def _get():
            return self._db.get(key)

        return await self._run_in_executor(_get)

    async def delete(self, key: Union[str, bytes]):
        def _delete():
            try:
                del self._db[key]
            except KeyError as ex:
                raise KeyError(f"Key {key} does not exist") from ex

        await self._run_in_executor(_delete)

    async def exists(self, key: Union[str, bytes]) -> bool:
        """Return True when the given key exists, else False."""

        def _exists():
            return key in self._db

        return await self._run_in_executor(_exists)

    async def keys(self) -> List[bytes]:
        """Return existing keys."""

        def _keys():
            return self._db.keys()

        return await self._run_in_executor(_keys)

    async def set(self, key: Union[str, bytes], value: Union[str, bytes]) -> None:
        """Set key to hold the value.
        If key already holds a value, it is overwritten.
        """

        def _set():
            self._db[key] = value

        await self._run_in_executor(_set)

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


""" ???
clear
close ?
items
update
values
"""


@asynccontextmanager
async def open(filename: Union[str, Path], flag="r", mode: int = 438):
    """Open the DBM database file and return a corresponding object."""

    def _open():
        return dbm.open(str(filename), flag, mode)  # type: ignore

    def _close(db):
        return db.close()

    loop = asyncio.get_running_loop()
    db = await loop.run_in_executor(None, _open)
    try:
        yield _DatabaseAsync(db, loop)
    finally:
        await loop.run_in_executor(None, _close, db)


async def whichdb(filename: Union[str, Path]) -> Optional[str]:
    """This function attempts to guess which of the several simple database modules
    available — dbm.gnu, dbm.ndbm or dbm.dumb — should be used to open a given file.

    Returns one of the following values:
    None if the file can't be opened because it's unreadable or doesn't exist;
    the empty string ('') if the file's format can't be guessed;
    or a string containing the required module name, such as 'dbm.ndbm' or 'dbm.gnu'.
    """

    def _whichdb():
        return dbm.whichdb(str(filename))

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _whichdb)
