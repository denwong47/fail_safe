# -*- coding: utf-8 -*-
"""
================================
 fail_safe
================================

A context manager class that retains data on error, and load from disk upon next execution.
"""

from . import decorators, utils

print("### Init had run for fail_safe ###")  # Remove this line
