# -*- coding: utf-8 -*-
"""
Timed decorators for functions.

Works with any Python callables, but this is primarily built for Rust imported
functions.
"""
import functools
from timeit import timeit
from typing import Any, Callable, ClassVar


class TimedResult(float):
    """
    An extended :class:`float` class that can also store the result of execution.

    This is for the purpose of :meth:`TimedFunction.timed` so that it can return both
    the duration of execution as well as its results.

    Parameters
    ----------
    value : Any
        The value to be converted to `float`.

    number : int
        Number of times that execution has been run.

    result : Any
        Optional. Result from the last execution of :class:`TimedFunction`.
    """

    number: int
    result: Any

    def __new__(cls, value: Any, *, number: int = 1, result: Any = None) -> None:
        return super().__new__(cls, value)

    def __init__(self, value: Any, *, number: int = 1, result: Any = None) -> None:
        super().__init__()
        self.number = number
        self.result = result

    @property
    def duration(self) -> float:
        """
        Alias for for ``float(self)``.

        Returns the duration of execution recorded when this instance initiated.
        """
        return float(self)

    @property
    def avg(self) -> "TimedResult":
        """
        Returns the average duration of execution for :class:`TimedFunction`.
        """
        return type(self)(self.duration / self.number, number=1, result=self.result)


class TimedFunction:
    """
    Decorator to add a `timed` method to the function.
    """

    _func: ClassVar[Callable]
    _last_returned: Any = None

    def __init__(self, func: Callable) -> None:
        self._func = func

    def uncached_call(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the underlying function without ``lru_cache``.

        Parameters
        ----------
        args, kwargs
            Parameters to be passed to the underlying function.

        Returns
        -------
        Any
            The return from the underlying function.
        """
        # Cache the last execution result
        self._last_returned = self._func(*args, **kwargs)
        return self._last_returned

    cached_call = functools.lru_cache(uncached_call)
    """
     Call the underlying function with ``lru_cache``.

        Parameters
        ----------
        args, kwargs
            Parameters to be passed to the underlying function.

        Returns
        -------
        Any
            The return from the underlying function.
    """

    # Default to cached call.
    __call__ = cached_call

    def timed(self, *args: Any, number: int = 1, **kwargs) -> TimedResult:
        """
        Run the underlying function, timed.

        Parameters
        ----------
        args, kwargs
            Parameters to be passed to the underlying function.

        number : int
            Number of executions to be run.

        Returns
        ------
        TimedResult
        """
        _duration = timeit(
            # When timing something, do not cache anything.
            lambda: self.uncached_call(*args, **kwargs),
            number=number,
        )

        return TimedResult(
            _duration,
            number=number,
            result=self._last_returned,
        )
