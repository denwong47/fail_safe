# -*- coding: utf-8 -*-
"""
Classes declared by this package.

These fall under two categories:

- :mod:`state` - Consists only :class:`FailSafeState`, the context manager class
  which is the main purpose of this package.
- :mod:`storage` - :class:`StateStorage` subclasses that performs the actual caching.
"""
from .state import FailSafeState
from .storage import LocalStorage, StateStorage
