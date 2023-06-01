import asyncio
import random
import time
import unittest
from functools import partial

from aiodbm.helpers import SingleWorkerThread

from .utils import random_strings


class TestSingleWorkerThread(unittest.IsolatedAsyncioTestCase):
    async def test_single_call(self):
        # given
        loop = asyncio.get_running_loop()
        thread = SingleWorkerThread(loop=loop)
        thread.start()
        # when
        result = await thread.run_soon_async(lambda: "DONE")
        # then
        self.assertEqual(result, "DONE")

    async def test_multiple_concurrent_calls(self):
        def worker(item):
            time.sleep(random.random() / 20)  # add jitter
            return item

        # given
        loop = asyncio.get_running_loop()
        thread = SingleWorkerThread(loop=loop)
        thread.start()
        # when
        items = random_strings(100)
        tasks = []
        for item in items:
            await asyncio.sleep(random.random() / 20)  # add jitter
            task = asyncio.create_task(thread.run_soon_async(partial(worker, item)))
            tasks.append(task)
        items_2 = await asyncio.gather(*tasks)

        # then
        self.assertSetEqual(set(items), set(items_2))

    async def test_should_reraise_exception_from_thread(self):
        def worker():
            raise RuntimeError("Test exception")

        # given
        loop = asyncio.get_running_loop()
        thread = SingleWorkerThread(loop=loop)
        thread.start()
        # when/then
        with self.assertRaises(RuntimeError):
            await thread.run_soon_async(worker)
