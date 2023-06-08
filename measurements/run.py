"""Measure and compare throughput between normal DBM and asyncio version."""

import asyncio
import datetime as dt
import json
import logging
import random
import string
import tempfile
import time
from abc import ABC, abstractmethod
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, Iterable, List

import aiosqlite

import aiodbm

logging.basicConfig(level="INFO", format="%(asctime)s|%(levelname)s|%(message)s")
logger = logging.getLogger(__name__)


class Timer:
    """A timer for measuring duration in seconds."""

    def __init__(self) -> None:
        self._start_sec = 0
        self._end_sec = 0

    @property
    def duration_sec(self) -> float:
        if not self._start_sec or not self._end_sec:
            raise ValueError("No complete measurement")
        return self._end_sec - self._start_sec

    def start(self):
        self._start_sec = time.perf_counter()

    def stop(self):
        self._end_sec = time.perf_counter()


def random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class Runner(ABC):
    name = "UNDEFINED"

    def __init__(self, items_amount, obj_size) -> None:
        if not items_amount or not obj_size:
            raise ValueError("Invalid params")

        self._items_amount = items_amount
        self._obj_size = obj_size
        self._read_seconds = None
        self._write_sec = None

    @property
    def items_amount(self):
        return self._items_amount

    @property
    def obj_size(self):
        return self._obj_size

    @property
    def read_throughput(self):
        if not self._read_seconds:
            raise ValueError("No measurement")
        return self.items_amount / self._read_seconds

    @property
    def write_throughput(self):
        if not self._write_sec:
            raise ValueError("No measurement")
        return self.items_amount / self._write_sec

    @abstractmethod
    async def measure_write(self, path: Path, objs: Dict[str, bytes], timer: Timer):
        pass

    @abstractmethod
    async def measure_read(
        self, path: Path, keys: Iterable[str], timer: Timer
    ) -> Dict[str, Any]:
        pass

    async def run(self):
        """Run measurements and return result as throughput in items / sec."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "measurement_2.dbm"
            objs = self.generate_objs()

            logger.info("%s: Start write measurements", self.name)
            timer_write = Timer()
            await self.measure_write(path, objs, timer_write)
            logger.info("%s: End write measurements", self.name)

            logger.info("%s: Start read measurements", self.name)
            timer_read = Timer()
            objs_2 = await self.measure_read(path, objs.keys(), timer_read)
            logger.info("%s: End read measurements", self.name)

            # print(objs)
            # print(objs_2)

            assert objs_2 == objs

        self._read_seconds = timer_read.duration_sec
        self._write_sec = timer_write.duration_sec

    def generate_objs(self) -> Dict[str, bytes]:
        objs = {
            f"item-{num:010}": random_string(self.obj_size).encode("utf-8")
            for num in range(1, self.items_amount + 1)
        }
        return objs

    def _identify_version(self) -> str:
        dist = metadata.distribution(self.name)
        return dist.version

    def result_out(self) -> str:
        return (
            f"{self.name}: Throughput with {self.items_amount:,} items: "
            f"read {self.read_throughput:,.1f} ops/sec, "
            f"write {self.write_throughput:,.1f} ops/sec"
        )

    def result_dict(self) -> dict:
        data = {
            "name": self.name,
            "version": self._identify_version(),
            "read_throughput": self.read_throughput,
            "write_throughput": self.write_throughput,
            "items_amount": self.items_amount,
            "object_size": self._obj_size,
            "timestamp": dt.datetime.utcnow().isoformat(),
        }
        return data


class DbmRunner(Runner):
    name = "aiodbm"

    async def measure_write(self, path, objs, timer):
        async with aiodbm.open(str(path), "c") as db:
            timer.start()
            for key, value in objs.items():
                await db.set(key, value)
            timer.stop()

    async def measure_read(self, path, keys, timer):
        objs_2: Dict[str, Any] = {}
        async with aiodbm.open(str(path), "c") as db:
            timer.start()
            for key in keys:
                objs_2[key] = await db.get(key)
            timer.stop()
        return objs_2


class SqliteRunner(Runner):
    name = "aiosqlite"

    async def measure_write(self, path, objs, timer):
        async with aiosqlite.connect(str(path), isolation_level=None) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS data (key TEXT PRIMARY KEY, value BLOB);"
            )
            timer.start()
            for key, value in objs.items():
                await db.execute(
                    "INSERT INTO data (key, value) VALUES (?, ?);", (key, value)
                )
            timer.stop()

    async def measure_read(self, path, keys, timer):
        objs_2: Dict[str, Any] = {}
        async with aiosqlite.connect(str(path), isolation_level=None) as db:
            timer.start()
            for key in keys:
                cursor = await db.execute(
                    "SELECT value FROM data WHERE key = (?);", (key,)
                )
                row = await cursor.fetchone()
                objs_2[key] = row[0] if row else None
            timer.stop()
        return objs_2


async def run_async(runners: Iterable[Runner]):
    for runner in runners:
        await runner.run()


def main():
    items_amount = 10_000
    object_size = 256
    runners: List[Runner] = [
        SqliteRunner(items_amount, object_size),
        DbmRunner(items_amount, object_size),
    ]

    asyncio.run(run_async(runners))

    for runner in runners:
        logger.info(runner.result_out())

    results = [runner.result_dict() for runner in runners]
    path = Path(__file__).parent / "measurements.json"
    with path.open("w") as file:
        json.dump(results, file)
    logger.info("Results written to %s", path)


if __name__ == "__main__":
    main()
