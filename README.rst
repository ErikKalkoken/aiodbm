======
aiodbm
======

A AsyncIO wrapper for Python's `DBM library <https://docs.python.org/3/library/dbm.html>`_.

|release| |python| |tests| |codecov| |docs| |pre-commit| |Code style: black|

Description
-----------

* Supports 100% of GDBM API
* Typing support
* Docstrings for all methods

To ensure DBM can be used safely with AsyncIO, all DB operations are serialized,
i.e. only one DB operation occurs at any given time.

This library is primarily made for GDBM, but should work with other implementations too.

Usage
-----

Here is a basic example on how to use the queue:

.. code:: python

    import asyncio

    import aiodbm


    async def main():
        async with aiodbm.open("data.dbm", "c") as db:  # opening/creating database
            await db.set("alpha", "green")  # creating new key alpha with value green
            value = await db.get("alpha")  # fetching value for key alpha
            print(value)
            await db.delete("alpha")  # delete key alpha


    asyncio.run(main())


Installation
------------

You can install this library directly from PyPI with the following command:

.. code:: shell

    pip install aiodbm


.. |release| image:: https://img.shields.io/pypi/v/aiodbm?label=release
   :target: https://pypi.org/project/aiodbm/
.. |python| image:: https://img.shields.io/pypi/pyversions/aiodbm
   :target: https://pypi.org/project/aiodbm/
.. |tests| image:: https://github.com/ErikKalkoken/aiodbm/actions/workflows/main.yml/badge.svg
   :target: https://github.com/ErikKalkoken/aiodbm/actions
.. |codecov| image:: https://codecov.io/gh/ErikKalkoken/aiodbm/branch/main/graph/badge.svg?token=V43h7hl1Te
   :target: https://codecov.io/gh/ErikKalkoken/aiodbm
.. |docs| image:: https://readthedocs.org/projects/aiodbm/badge/?version=latest
   :target: https://aiodbm.readthedocs.io/en/latest/?badge=latest
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
