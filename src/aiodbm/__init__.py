"""An AsyncIO bridge for DBM."""

__version__ = "0.4.2"

from .core import Database, error, open, whichdb

__all__ = ["open", "Database", "whichdb", "error"]
