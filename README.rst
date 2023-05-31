======
aiodbm
======

A AsyncIO wrapper for Python's DBM library.

* Supports 100% of GDBM API
* Typing support
* Docstrings for all methods

Since all operations need to be awaited this API uses normal methods instead of dict like operations,
e.g. get for fetching a value from a key and set to store it.

This library is made for GDBM (the mostly used DBM implementation on Linux),
so some method might fail when GDBM is not available.
