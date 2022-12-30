### Read Me for
# Fail Safe Context Manager

![CI Checks](https://github.com/denwong47/fail_safe/actions/workflows/CI.yml/badge.svg?branch=main)

> ## **Documentation**:
>
> **Available at [github pages](https://denwong47.github.io/fail_safe/).**

A context manager class that retains data on error, and load from disk upon next execution.

A context manager class that retains data on error, and load from disk upon next execution.

Context manager that caches local scope upon exceptions; loads for next execution.

This class is for iterations over non-Generator iterators that has a high risk of
failure (e.g. over unsanitised data). Within the context of a
`FailSafeState`, any unhandled exceptions will cause `FailSafeState`
to write the attached local variables to `StateStorage`. When re-running the
same context, `FailSafeState` will look for pickled data from last time,
and load the last exception state into `locals`, so the iteration does not
need to start from fresh.

For example::

```py

from fail_safe import FailSafeState, LocalStorage

unclean_data = [ "a", "b", "c", "d" ]
cleaned_data = {}

with (
    FailSafeState()
    .uses(LocalStorage())
    .attach("cleaned_data")
) as state:
    # 1st execution:         `FailSafeState` did not find any stored state,
    #                        `cleaned_data` is unchanged.
    # Subsequent executions: a saved sate is found, `cleaned_data` is replaced.

    for _id, _data in enumerate(unclean_data):

        # This ensures that we won't repeat whatever we already have cleaned.
        if _id not in cleaned_data:
            # Assume this function may throw unhandled exceptions
            # because we can't foresee all of the possible errors;
            # e.g. webscrapping.
            #
            # Assuming this caused an error on 1st execution.
            cleaned_data[_id] = some_risky_cleaning_func(_data)

    # 1st execution:         `FailSafeState` found an unhandled exception,
    #                        and saved `cleaned_data` to `LocalStorage()`
    #                        before raising the error.
    # Subsequent executions: Assuming execution was successful, `FailSafeState`
    #                        wipes any saved state files.

```
