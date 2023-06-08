=======================
aiodbm: DBM for AsyncIO
=======================

An AsyncIO bridge for Python's DBM library.

|release| |python| |tests| |codecov| |docs| |pre-commit| |Code style: black|

Description
-----------

aiodbm is a library that allows you to use DBM in asyncio code.

* Full coverage of Python's DBM and GDBM API
* Typing support
* Docstrings and documentation
* Fully tested

Why use DBM?
---------------

`DBM <https://en.wikipedia.org/wiki/DBM_(computing)>`_ is a fast and easy to use, embedded key-value store.
It is supported by Python's standard library [1]_ and can be used on most systems without requiring additional dependencies [2]_.

Compared to Sqlite - the other embedded database supported by Python's standard library - it is significantly faster when used as key/value store.

According to our measurement we see that aiodbm is about 140x faster on writes and about 3.5x faster on reads [3]_ on Linux:

.. image:: measurements/measurements.png
  :width: 800
  :alt: Throughput measurements for aiodbm vs. aiosqlite

So if you want to are looking for a fast and an easy to use key-value store (e.g. for caching) on Linux systems, DBM can be a good solution.

Caveats
-------

On non Linux-like systems Python might use it's "dumb" DBM implementation, which will be much slower.

DBM is not process safe. If you need a key-value store in a multi process context (e.g. a web server running with gunicorn) we'd recommend to use Redis or something similar instead.

Usage
-----

Here is a basic example on how to use the library:

.. code:: python

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


Installation
------------

You can install this library directly from PyPI with the following command:

.. code:: shell

    pip install aiodbm

------------

Reference
---------

.. [1] See also Python's DBM module: https://docs.python.org/3/library/dbm.html

.. [2] The newer DBM variants GDBM or NDBM are preinstalled on most Linux/Unix systems: https://en.wikipedia.org/wiki/DBM_(computing)#Availability

.. [3] We compared the asyncio versions with 10.000 write and read operations of key/value pairs on Linux with GDBM. See also measurements folder for more details.

.. _DBM: https://en.wikipedia.org/wiki/DBM_(computing)
.. _benchmark: https://charlesleifer.com/blog/completely-un-scientific-benchmarks-of-some-embedded-databases-with-python/

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
