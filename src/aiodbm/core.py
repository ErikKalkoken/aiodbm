import asyncio
import dbm
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Union


class DbmAsync:
    """An async wrapper for a DBM database."""

    def __init__(self, db, loop: asyncio.AbstractEventLoop) -> None:
        self._db = db
        self._loop = loop

    async def set(self, key: Union[str, bytes], value: Union[str, bytes]) -> None:
        await self._loop.run_in_executor(None, self._set, self._db, key, value)

    @staticmethod
    def _set(db, key, value):
        db[key] = value

    async def get(self, key: Union[str, bytes]) -> bytes:
        return await self._loop.run_in_executor(None, self._get, self._db, key)

    @staticmethod
    def _get(db, key):
        return db.get(key)

    async def setdefault(self, key: Union[str, bytes], default: bytes) -> bytes:
        return await self._loop.run_in_executor(
            None, self._setdefault, self._db, key, default
        )

    @staticmethod
    def _setdefault(db, key, default):
        return db.setdefault(key, default)

    async def delete(self, key: Union[str, bytes]):
        await self._loop.run_in_executor(None, self._delete, self._db, key)

    @staticmethod
    def _delete(db, key):
        del db[key]

    async def has_key(self, key: Union[str, bytes]) -> bool:
        return await self._loop.run_in_executor(None, self._has_key, self._db, key)

    @staticmethod
    def _has_key(db, key):
        return key in db

    async def keys(self) -> List[bytes]:
        return await self._loop.run_in_executor(None, self._keys, self._db)

    @staticmethod
    def _keys(db):
        return db.keys()


""" ???
clear
close ?
items
update
values
"""


@asynccontextmanager
async def open(filename: Union[str, Path], flag="r", mode: int = 438):
    def _open(filename):
        return dbm.open(str(filename), flag, mode)  # type: ignore

    def _close(db):
        return db.close()

    loop = asyncio.get_running_loop()
    db = await loop.run_in_executor(None, _open, filename)
    try:
        yield DbmAsync(db, loop)
    finally:
        await loop.run_in_executor(None, _close, db)


async def whichdb(filename: Union[str, Path]) -> str:
    def _whichdb(filename):
        return dbm.whichdb(str(filename))

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _whichdb, filename)


def test():
    with dbm.open("xxx") as db:
        db.setdefault("aa", b"bj")
