import asyncio
import time
import unittest
from unittest.mock import Mock

from aiodbm.threads import ThreadRunner, _Message


class TestThreadRunnerBasics(unittest.TestCase):
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

    def test_should_raise_error_when_trying_to_schedule_work_while_not_running(self):
        # given
        thread = ThreadRunner()
        # when/then
        with self.assertRaises(RuntimeError):
            thread.call_soon(Mock(), Mock)


class TestThreadRunnerWork(unittest.TestCase):
    def setUp(self) -> None:
        self.thread = ThreadRunner()
        self.thread.start()

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
