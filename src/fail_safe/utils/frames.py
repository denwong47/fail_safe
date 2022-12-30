# -*- coding: utf-8 -*-
"""

"""

import ctypes
import inspect


def get_caller_locals(*, f_back_levels: int = 1):

    assert f_back_levels > 0
    frame = inspect.currentframe()

    for _ in range(f_back_levels):
        frame = frame.f_back

    return frame.f_locals


def set_caller_locals(*, f_back_levels: int = 1, **kwargs: dict):

    assert f_back_levels > 0
    frame = inspect.currentframe()

    for _ in range(f_back_levels):
        frame = frame.f_back

    frame.f_locals.update(kwargs)

    # Mystical C-level hackery by PyDev:
    # https://pydev.blogspot.com/2014/02/changing-locals-of-frame-frameflocals.html
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))
