import asyncio

import aiodbm


async def main():
    # opening/creating database
    async with aiodbm.open("example.dbm", "c") as db:
        # creating new key alpha with value green
        await db.set("alpha", "green")

        # fetching value for key alpha
        value = await db.get("alpha")
        print(value)

        # delete key alpha
        await db.delete("alpha")


asyncio.run(main())
