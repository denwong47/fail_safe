# -*- coding: utf-8 -*-
"""
================================
 fail_safe
================================

A context manager class that retains data on error, and load from disk upon next execution.
"""

from . import classes, utils
from .classes import FailSafeState, LocalStorage, StateStorage, storage
