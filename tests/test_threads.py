import asyncio
import unittest

from aiodbm.threads import _Message


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
