"""An AsyncIO bridge for DBM."""

__version__ = "0.2.0a1"

from .core import Database, open, whichdb

__all__ = ["open", "Database", "whichdb"]
