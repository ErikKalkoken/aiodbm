"""An AsyncIO bridge for DBM."""

__version__ = "0.3.0"

from .core import Database, open, whichdb

__all__ = ["open", "Database", "whichdb"]
