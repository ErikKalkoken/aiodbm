"""A AsyncIO wrapper for DBM."""

__version__ = "0.2.0a1"

from .core import DbmDatabase, open, whichdb

__all__ = ["open", "DbmDatabase", "whichdb"]
