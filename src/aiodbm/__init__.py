"""A AsyncIO wrapper for DBM."""

__version__ = "0.1.0dev1"

from .core import open, whichdb

__all__ = ["open", "whichdb"]
