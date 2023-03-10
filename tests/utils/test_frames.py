# -*- coding: utf-8 -*-
import random

import pytest

from fail_safe.utils import frames


def test_frames_get_and_set():
    def some_useful_func_that_uses_current_locals():
        return frames.get_caller_locals()

    def some_useful_func_that_sets_current_locals(**kwargs):
        return frames.set_caller_locals(**kwargs)

    # Define some variables
    local_int = random.randint(0, 2**32)
    local_str = "%08x" % random.randint(0, 2**32)
    local_bytes = random.randbytes(32)
    local_list = [random.randint(0, 2**32) for _ in range(32)]
    local_dict = {i: random.randint(0, 2**32) for i in range(32)}
    local_iter = filter(lambda x: x > 2**31, map(lambda x: 2 * x, local_list))

    _var_names = tuple(filter(lambda key: key.startswith("local_"), locals()))

    # Simulate a function
    old_locals = locals().copy()

    get_locals = some_useful_func_that_uses_current_locals()
    for _var_name in _var_names:
        assert _var_name in get_locals

    for key, value in get_locals.items():
        if key.startswith("local_"):
            # Check that we fetched the values correctly
            assert value == old_locals.get(key)

    # Re-define variables
    local_int = -random.randint(0, 2**32)
    local_str = "A different string"
    local_bytes = random.randbytes(16)
    local_list = [-random.randint(0, 2**32) for _ in range(32)]
    local_dict = {i: -random.randint(0, 2**32) for i in range(32)}
    local_iter = filter(lambda x: x < -(2**31), map(lambda x: 2 * x, local_list))

    get_locals = some_useful_func_that_uses_current_locals()
    for _var_name in _var_names:
        assert _var_name in get_locals

    for key, value in get_locals.items():
        if key.startswith("local_"):
            # Check that they are now the new values
            assert value != old_locals.get(key)

    # Reset variables
    some_useful_func_that_sets_current_locals(**old_locals)

    get_locals = locals()
    for _var_name in _var_names:
        assert _var_name in get_locals
    for key, value in get_locals.items():
        if key.startswith("local_"):
            # Check that they are reverted back to the old values
            assert value == old_locals.get(key)

    # Set variable inside function
    def my_func(value: int):
        def extra_level():
            frames.set_caller_locals(f_back_levels=3, local_int=value)

        extra_level()

    # Check that the variable is now the new value
    my_func((new_int := random.randint(0, 2 * 32)))

    assert local_int == new_int
