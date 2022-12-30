# -*- coding: utf-8 -*-
"""
Frame walking utilities.

Allow getting and setting of local variables at upper scopes

.. warning::
    The inner working of this module is not deemed "safe"; they are intended
    for internal use in specific scenarios.

    Do not use outside of this package.
"""

import ctypes
import inspect
from typing import Any, Dict

UPPER_LEVEL: int = 3
CALLER_LEVEL: int = 2
LOCAL_LEVEL: int = 1


def get_caller_locals(*, f_back_levels: int = CALLER_LEVEL) -> Dict[str, Any]:
    """
    Getting local variables at upper scopes.

    .. warning::
        The inner working of this function is not deemed "safe"; they are intended
        for internal use in specific scenarios.

        Do not use outside of this package.

    Parameters
    ----------
    f_back_levels: int = CALLER_LEVEL
        Optional. The number of frames to walk back before getting the locals;
        must be >`0`.

        An illustration of a sample script::

            from fail_safe.utils import frames

            def my_func():
                # f_back_levels = 1

                my_var = "my_func level"

                assert (
                    frames.get_caller_locals(f_back_levels = 1)["my_var"]
                    == "my_func level"
                )
                assert (
                    frames.get_caller_locals(f_back_levels = 2)["my_var"]
                    == "main level"
                )

                # Defaults to the caller of the current function,
                # since `f_back_levels=1` is simply the current locals!
                assert frames.get_caller_locals()["my_var"] == "main level"

            def main():
                # f_back_levels = 2
                my_var = "main level"

                my_func()

            if __name__=="__main__":
                main()

    Returns
    -------
    Dict[str, Any]
        Local variables of the level required.
    """
    assert f_back_levels > 0, (
        "Number of frames walking should be >0. "
        "0 is the context within `get_caller_locals`, "
        "1 being the caller of `get_caller_locals`, "
        "2 being the called of the current function (default), etc."
    )
    frame = inspect.currentframe()

    for _ in range(f_back_levels):
        frame = frame.f_back

    return frame.f_locals


def set_caller_locals(*, f_back_levels: int = CALLER_LEVEL, **kwargs: dict):
    """
    Updating local variables at upper scopes.

    This does *NOT* remove variables; it simply updates and adds to the local scope in
    question.

    .. warning::
        The inner working of this function is not deemed "safe"; they are intended
        for internal use in specific scenarios.

        Do not use outside of this package.

    Parameters
    ----------
    f_back_levels: int = CALLER_LEVEL
        Optional. The number of frames to walk back before getting the locals;
        must be >`0`.

        An illustration of a sample script::

            from fail_safe.utils import frames

            def my_func():
                # f_back_levels = 1

                my_var = "my_func level"

                assert (
                    frames.get_caller_locals(f_back_levels = 1)["my_var"]
                    == "my_func level"
                )
                assert (
                    frames.get_caller_locals(f_back_levels = 2)["my_var"]
                    == "main level"
                )

                # Defaults to the caller of the current function,
                # since `f_back_levels=1` is simply the current locals!
                assert frames.get_caller_locals()["my_var"] == "main level"

            def main():
                # f_back_levels = 2
                my_var = "main level"

                my_func()

            if __name__=="__main__":
                main()

    kwargs
        Variables to set, expanded as keyword arguments.
    """
    assert f_back_levels > 0, (
        "Number of frames walking should be >0. "
        "0 is the context within `get_caller_locals`, "
        "1 being the caller of `get_caller_locals`, "
        "2 being the called of the current function (default), etc."
    )
    frame = inspect.currentframe()

    for _ in range(f_back_levels):
        frame = frame.f_back

    frame.f_locals.update(kwargs)

    # Mystical C-level hackery by PyDev:
    # https://pydev.blogspot.com/2014/02/changing-locals-of-frame-frameflocals.html
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))


def get_caller_name(*, f_back_levels: int = CALLER_LEVEL) -> str:
    """
    Attempt to the name of the caller.

    If its a module, returns the qualified name of the module.
    Otherwise, return the function name that is running.
    """
    frame = inspect.currentframe()

    for _ in range(f_back_levels):
        frame = frame.f_back

    if frame:
        if "__qualname__" in frame.f_locals:
            return frame.f_locals.get("__qualname__")
        elif "__name__" in frame.f_locals:
            return frame.f_locals.get("__name__")
        else:
            return frame.f_code.co_name

    return None
