import asyncio
import time
import unittest
from unittest.mock import Mock

from aiodbm.threads import ThreadRunner, _Message


class TestThreadRunnerBasics(unittest.IsolatedAsyncioTestCase):
    def test_can_create(self):
        # when
        thread = ThreadRunner()
        # then
        self.assertIsInstance(thread, ThreadRunner)
        self.assertFalse(thread.is_alive())

    def test_can_start_and_stop(self):
        # given
        thread = ThreadRunner()
        # when
        thread.start()
        self.assertTrue(thread.is_alive())
        thread.stop()
        time.sleep(1)
        self.assertFalse(thread.is_alive())

    async def test_should_raise_error_when_trying_to_schedule_work_while_not_running(
        self,
    ):
        # given
        thread = ThreadRunner()
        # when/then
        with self.assertRaises(RuntimeError):
            await thread.call_soon(Mock)


class TestThreadRunnerWork(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.thread = ThreadRunner()
        self.thread.start()

    async def test_should_run_function_in_thread(self):
        def my_func():
            return 42

        # when
        result = await self.thread.call_soon(my_func)
        # then
        self.assertEqual(result, 42)

    async def test_should_propagate_exception_when_occurred_in_function_call(self):
        def my_func():
            raise ValueError("Test exception")

        # when/then
        with self.assertRaises(ValueError):
            await self.thread.call_soon(my_func)

    async def test_should_raise_error_when_not_a_callable(self):
        # when/then
        with self.assertRaises(TypeError):
            await self.thread.call_soon("dummy")  # type: ignore

    def tearDown(self) -> None:
        self.thread.stop()


class TestMessage(unittest.IsolatedAsyncioTestCase):
    async def test_str(self):
        def alpha():
            pass

        # given
        future = asyncio.get_running_loop().create_future()
        message = _Message(future, alpha)
        # then
        self.assertIn("alpha", str(message))

    def test_can_create_stop_signal(self):
        # when
        message = _Message.create_stop_signal()
        # then
        self.assertTrue(message.is_stop_signal)

    def test_future_strict_raises_error_when_no_future(self):
        # given
        message = _Message.create_stop_signal()
        # when/then
        with self.assertRaises(ValueError):
            message.future_strict

    def test_func_strict_raises_error_when_no_func(self):
        # given
        message = _Message.create_stop_signal()
        # when/then
        with self.assertRaises(ValueError):
            message.func_strict
