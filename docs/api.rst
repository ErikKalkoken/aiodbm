.. currentmodule:: aiodbm

===============
API Reference
===============

.. automodule:: aiodbm

.. autodata:: error

    A tuple containing the exceptions that can be raised by each
    of the supported modules,
    with a unique exception also named dbm.error as the first item —
    the latter is used when dbm.error is raised.

    Example usage:

    .. code-block:: Python

        try:
            async with open("example.dbm", "c") as db:
                ...
        except aiodbm.error as ex:
            print(f"Error when trying to open the database: {ex}")
