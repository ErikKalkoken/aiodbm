======
aiodbm
======

A AsyncIO wrapper for Python's `DBM library <https://docs.python.org/3/library/dbm.html>`_.

* Supports 100% of GDBM API
* Typing support
* Docstrings for all methods

To ensure DBM can be used "concurrently" with AsyncIO, all DB operations are serialized,
i.e. only one DB operation occurs at any given time.

This library is primarily made for GDBM, but should work with other implementations too.
