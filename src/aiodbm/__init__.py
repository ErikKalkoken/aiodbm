"""A AsyncIO wrapper for DBM."""

__version__ = "0.2.0dev1"

from .core import DbmDatabase, open, whichdb

__all__ = ["open", "DbmDatabase", "whichdb"]
