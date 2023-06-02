"""Measure and compare throughput between normal DBM and asyncio version."""

import asyncio
import dbm
import random
import string
import tempfile
import time
from pathlib import Path

import aiodbm

ITEMS_AMOUNT = 10_000
OBJECT_SIZE = 256


def random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_objs() -> dict:
    objs = {
        f"item-{num:010}": random_string(OBJECT_SIZE)
        for num in range(1, ITEMS_AMOUNT + 1)
    }
    return objs


def run_normal():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "measurement_1.dbm"
        objs = generate_objs()
        objs_2 = {}
        with dbm.open(str(path), "c") as db:
            start = time.perf_counter()
            for key, value in objs.items():
                db[key] = value
            for key in objs.keys():
                objs_2[key] = db[key]
            end = time.perf_counter()

    duration = end - start
    return duration


async def run_async():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "measurement_2.dbm"
        objs = generate_objs()
        objs_2 = {}
        async with aiodbm.open(str(path), "c") as db:
            start = time.perf_counter()
            for key, value in objs.items():
                await db.set(key, value)
            for key in objs.keys():
                objs_2[key] = await db.get(key)

            end = time.perf_counter()

    duration = end - start
    return duration


def main():
    throughput_normal = ITEMS_AMOUNT / run_normal()
    print(f"Throughput measurement results for {ITEMS_AMOUNT:,} items:")
    print(f"Normal: {throughput_normal:,.1f} items / sec")

    throughput_async = ITEMS_AMOUNT / asyncio.run(run_async())
    print(f"Async: {throughput_async:,.1f} items / sec")
    factor = int(throughput_async / throughput_normal * 100)
    print(f"Throughput of async version is {factor}% of normal")


if __name__ == "__main__":
    main()
