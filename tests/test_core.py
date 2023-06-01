import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import aiodbm

python_version = f"{sys.version_info.major}{sys.version_info.minor}"


class DbmAsyncioTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_path = str(self.temp_dir / "data.dbm")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestDbmFunctions(DbmAsyncioTestCase):
    async def test_whichdbm_should_return_name(self):
        # given
        async with aiodbm.open(self.data_path, "c") as db:
            await db.set("alpha", "green")

        # when
        result = await aiodbm.whichdb(self.data_path)
        # then
        self.assertIn(result, ["dbm.gnu", "dbm.ndbm", "dbm.dumb"])


class TestDatabaseAsync(DbmAsyncioTestCase):
    async def test_get_should_return_none_when_key_does_not_exists(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when
            result = await db.get("alpha")
            # then
            self.assertIsNone(result)

    async def test_get_should_return_default_when_key_does_not_exists(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when
            result = await db.get("alpha", b"yellow")
            # then
            self.assertEqual(result, b"yellow")

    async def test_close_should_close_the_db(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when/then
            await db.close()

    async def test_delete_should_remove_entry(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "blue")
            # when
            await db.delete("alpha")
            # then
            self.assertFalse(await db.exists("alpha"))

    async def test_delete_should_raise_error_when_key_does_not_exist(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when/then
            with self.assertRaises(KeyError):
                await db.delete("alpha")

    async def test_exists_returns_true_when_key_exists(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "blue")
            # when/then
            self.assertTrue(await db.exists("alpha"))

    async def test_exists_returns_false_when_key_does_not_exists(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when/then
            self.assertFalse(await db.exists("alpha"))

    async def test_keys_should_return_existing_keys(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "blue")
            await db.set("bravo", "red")
            # when
            result = await db.keys()
            # then
            self.assertSetEqual(set(result), {b"bravo", b"alpha"})

    async def test_keys_should_return_empty_list_when_no_keys(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when
            result = await db.keys()
            # then
            self.assertListEqual(result, [])

    async def test_set_should_create_new_entry(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when
            await db.set("alpha", "blue")
            # then
            data = await db.get("alpha")
        self.assertEqual(data, b"blue")

    async def test_set_should_overwrite_existing_entry(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "blue")
            # when
            await db.set("alpha", "yellow")
            # then
            data = await db.get("alpha")
            self.assertEqual(data, b"yellow")

    async def test_set_should_add_a_new_entry(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when
            await db.set("alpha", "blue")
            # then
            data = await db.get("alpha")
            self.assertEqual(data, b"blue")

    async def test_set_should_raise_error_on_wrong_types(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when/then
            with self.assertRaises(TypeError):
                await db.set("alpha", 1)  # type: ignore

    async def test_setdefault_should_add_new_entry_when_key_does_not_exit(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when
            result = await db.setdefault("alpha", b"blue")
            # then
            self.assertEqual(result, b"blue")

    async def test_setdefault_should_return_existing_value_when_key_exists(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "green")
            # when
            result = await db.setdefault("alpha", b"blue")
            # then
            self.assertEqual(result, b"green")


@unittest.skipIf(python_version in ["38", "39"], reason="Unsupported Python")
class TestGdbmFunctions(DbmAsyncioTestCase):
    async def test_firstkey_should_return_first_key(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "green")
            # when
            result = await db.firstkey()
            # then
            self.assertEqual(result, b"alpha")

    async def test_can_loop_though_all_keys(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # given
            await db.set("alpha", "green")
            await db.set("bravo", "green")
            await db.set("charlie", "green")
            # when
            keys = set()
            key = await db.firstkey()
            while key is not None:
                keys.add(key)
                key = await db.nextkey(key)
            # then
            self.assertSetEqual(keys, {b"alpha", b"bravo", b"charlie"})

    async def test_can_reorganize(self):
        async with aiodbm.open(self.data_path, "c") as db:
            # when/then
            await db.reorganize()

    async def test_can_sync(self):
        async with aiodbm.open(self.data_path, "cf") as db:
            # when/then
            await db.set("alpha", "green")
            await db.sync()
