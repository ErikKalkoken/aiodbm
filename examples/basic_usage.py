import asyncio

import aiodbm


async def main():
    async with aiodbm.open("data.dbm", "c") as db:  # opening/creating database
        await db.set("alpha", "green")  # creating new key alpha with value green
        value = await db.get("alpha")  # fetching value for key alpha
        print(value)
        await db.delete("alpha")  # delete key alpha


asyncio.run(main())
