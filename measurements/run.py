"""Measure and compare throughput between normal DBM and asyncio version."""

import asyncio
import random
import string
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path

import aiosqlite

import aiodbm

ITEMS_AMOUNT = 10_000
OBJECT_SIZE = 256


def random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class Runner(ABC):
    @abstractmethod
    async def do_work(self, path, objs):
        pass

    async def run(self) -> float:
        """Run measurements and return result as throughput in items / sec."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "measurement_2.dbm"
            objs = self.generate_objs()

            start = time.perf_counter()
            objs_2 = await self.do_work(path, objs)
            end = time.perf_counter()

            # print(objs)
            # print(objs_2)

            assert objs_2 == objs

        duration = end - start
        return ITEMS_AMOUNT / duration

    @staticmethod
    def generate_objs() -> dict:
        objs = {
            f"item-{num:010}": random_string(OBJECT_SIZE).encode("utf-8")
            for num in range(1, ITEMS_AMOUNT + 1)
        }
        return objs


class DbmRunner(Runner):
    async def do_work(self, path, objs):
        objs_2 = {}
        async with aiodbm.open(str(path), "c") as db:
            for key, value in objs.items():
                await db.set(key, value)
            for key in objs.keys():
                objs_2[key] = await db.get(key)
        return objs_2


class SqliteRunner(Runner):
    async def do_work(self, path, objs):
        objs_2 = {}
        async with aiosqlite.connect(str(path)) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS data (key TEXT PRIMARY KEY, value BLOB);"
            )
            for key, value in objs.items():
                await db.execute(
                    "INSERT INTO data (key, value) VALUES (?, ?);", (key, value)
                )

            for key in objs.keys():
                cursor = await db.execute(
                    "SELECT value FROM data WHERE key = (?);", (key,)
                )
                row = await cursor.fetchone()
                objs_2[key] = row[0]  # type: ignore
        return objs_2


async def main():
    # throughput_normal = ITEMS_AMOUNT / await run_sqlite_async()
    # print(f"Throughput measurement results for {ITEMS_AMOUNT:,} items:")
    # print(f"Sqlite: {throughput_normal:,.1f} items / sec")

    # throughput_async = ITEMS_AMOUNT / asyncio.run(run_dbm_async())
    # print(f"Async: {throughput_async:,.1f} items / sec")
    # factor = int(throughput_async / throughput_normal * 100)
    # print(f"Throughput of async version is {factor}% of normal")

    sqlite = await SqliteRunner().run()
    dbm = await DbmRunner().run()
    factor = dbm / sqlite
    print(f"Throughput measurement results for {ITEMS_AMOUNT:,} items:")
    print(f"Sqlite: {sqlite:,.1f}")
    print(f"Dbm:    {dbm:,.1f} ({factor:.1f}x)")


if __name__ == "__main__":
    asyncio.run(main())
