# -*- coding: utf-8 -*-
"""
State classes.

Context manager class that performs the fail safe operations.
"""
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, Type, Union

from ..utils import frames
from . import storage


class FailSafeState:
    """
    Context manager that caches local scope upon exceptions; loads for next execution.

    This class is for iterations over non-Generator iterators that has a high risk of
    failure (e.g. over unsanitised data). Within the context of a
    :class:`FailSafeState`, any unhandled exceptions will cause :class:`FailSafeState`
    to write the attached local variables to `StateStorage`. When re-running the
    same context, :class:`FailSafeState` will look for pickled data from last time,
    and load the last exception state into :func:`locals`, so the iteration does not
    need to start from fresh.

    For example::

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

    .. note::
        The following types are notably not supported:

        - Generators
        - :meth:`pandas.DataFrame.iterrows` - this is in fact a Generator.

    .. note::
        Ensure you attach the :func:`iter` wrapped object instead of a :class:`list`,
        :class:`dict` or :class:`tuple`.

        For example, this will **NOT** work::

            from fail_safe import FailSafeState, LocalStorage

            my_list = [ 0, 1, 2, 3 ]

            with (
                FailSafeState()
                .uses(LocalStorage())
                .attach("my_list")
            ) as state:
                # Assume something causes an error the first time round after
                # we iterated two elements:
                next(my_list)
                next(my_list)

                # Upon second execution, `next(my_list)` will start iterating from index
                # `0` again, because `my_list` does not store any iteration pointers.

        Instead, the :func:`iter` of ``my_list`` should be passed::

            from fail_safe import FailSafeState, LocalStorage

            my_list = [ 0, 1, 2, 3 ]
            my_list_iter = iter(my_list)

            with (
                FailSafeState()
                .uses(LocalStorage())
                .attach("my_list_iter")
            ) as state:
                # Assume something causes an error the first time round after
                # we iterated two elements:
                next(my_list_iter)
                next(my_list_iter)

                # Upon second execution, `my_list_iter` will remember the last value it
                # yielded and restart from that position.

    .. warning::
        This approach is not without its nuances; mainly to do with the item which
        causes the error in the first place had already been yielded by the iterator,
        and there is no easy way to put it back.

        If we are to re-run the script, the erroring element would be missed.

        Thus it is recommended to rebuild the iterator using the output variables,
        before resuming the iterator.

    """

    name: str

    attached: List[Any]
    state_stores: List[storage.StateStorage]
    delete_cache: bool

    def __init__(
        self,
        name: str = None,
        *,
        attach: List[str] = None,
        uses: List[storage.StateStorage] = None,
        delete_cache: bool = storage.DELETE,
    ):
        if not name:
            name = f"savedstate_{frames.get_caller_name()}"

        self.name = name

        self.attached = []
        self.state_stores = []

        if attach:
            self.attach(*attach)

        if uses:
            self.uses(*uses)

        self.delete_cache = delete_cache

    def __enter__(self) -> "FailSafeState":

        if not self.state_stores:
            raise ValueError(
                "No `StateStorage` registered; `FailSafeState` has nowhere to store "
                "local state upon exception. Use `.uses()` to add `StateStorage` "
                "instances."
            )

        _loaded_state = self.load_state()

        if isinstance(_loaded_state, dict):
            frames.set_caller_locals(**self.filter_vars(_loaded_state))

        self._entered = True

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_instance: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> bool:
        self._entered = False

        if (
            isinstance(exc_type, type)
            and isinstance(exc_instance, BaseException)
            or not self.delete_cache
        ):
            _suspend_state = self.filter_vars(frames.get_caller_locals())

            self.save_state(_suspend_state)
        else:
            self.del_state()

        return False

    def attach(self, *args: str) -> "FailSafeState":
        """
        Attach variables by :class:`str` name into the state.

        Parameters
        ----------
        args
            Any number of :class:`str`, each being the name of a local variable that
            needs to be saved on error.

            Any names that are already attached will be ignored.

        Returns
        -------
        FailSafeState
            Returns itself so that these functions can be chained.
        """
        for arg in args:
            if not isinstance(arg, str):
                raise TypeError(
                    "`attach` only accepts `str` as arguments; did you pass in the "
                    "variable itself as opposed to its name (e.g. `'my_list'` vs"
                    f"`my_list`)? Found value: {repr(arg)}"
                )

            if arg not in self.attached:
                self.attached.append(arg)

        return self

    def detach(self, *args: str) -> "FailSafeState":
        """
        Detach variables by :class:`str` name from the state.

        Parameters
        ----------
        args : str
            Any number of :class:`str`, each being the name of a local variable that
            needs to be removed from the :class:`FailSafeState` instance.

            Any names that are not already attached will be ignored.

        Returns
        -------
        FailSafeState
            Returns itself so that these functions can be chained.
        """
        for arg in args:
            if arg in self.attached:
                self.attached.remove(arg)

        return self

    def uses(self, *storages: storage.StateStorage) -> "FailSafeState":
        """
        Adds storages to this instance.

        Parameters
        ----------
        storages : ~fail_safe.classes.storage.StateStorage
            Any number of :class:`~fail_safe.classes.storage.StateStorage`, in
            decreasing order of priority.

            They will all be written to upon error, but when loading, the first storage
            that returns a state will be used, and the rest disregarded.

        Returns
        -------
        FailSafeState
            Returns itself so that these functions can be chained.

        Raises
        ------
        TypeError
            If any of ``storages`` is not an instance of
            :class:`~fail_safe.classes.storage.StateStorage`.
        """
        for store in storages:
            if not isinstance(store, storage.StateStorage):
                raise TypeError(
                    f"All storages for {type(self).__name__} should be `StateStorage` "
                    f"instances; but {repr(store)} found."
                )

            if store not in self.state_stores:
                self.state_stores.append(store)

        return self

    def filter_vars(self, locals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter to variables that are attached.

        **Internal function**. If there is nothing attached, all local variables are
        included.
        """
        if self.attached:
            return {key: value for key, value in locals.items() if key in self.attached}
        else:
            return locals

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Attempt to load a state from storage.

        **Internal function**. Use context manager (i.e. ``with`` statements) instead.
        """
        for store in self.state_stores:
            _loaded_state = store.load(self.name)

            if _loaded_state is not None:
                return _loaded_state

        return None

    def save_state(self, state: Dict[str, Any]):
        """
        Save a state to storage.

        **Internal function**. Use context manager (i.e. ``with`` statements) instead.
        """
        with ThreadPoolExecutor() as executor:
            for _ in executor.map(
                lambda store: store.save(self.name, state), self.state_stores
            ):
                pass

    def del_state(self):
        """
        Remove all states from storage.

        **Internal function**. Use context manager (i.e. ``with`` statements) instead.
        """
        with ThreadPoolExecutor() as executor:
            for _ in executor.map(
                lambda store: store.wipe(self.name), self.state_stores
            ):
                pass

    wipe = del_state
    """
    Alias for :meth:`del_state`.
    """

    def when_complete(self, delete_cache: bool = storage.DELETE) -> "FailSafeState":
        """
        State what to do when the context exits successfully.

        By default, all saved states will be wiped upon successful exit of the context.
        In some scenarios, we may want to keep them around (i.e. paid APIs) until a
        forced update is required.

        Setting ``delete_cache`` to :attr:`~fail_safe.classes.storage.RETAIN` will
        allow the cache to persist.

        Parameters
        ----------
        delete_cache : bool
            To delete cache or not when context exits successfully.

        Returns
        -------
        FailSafeState
            Returns itself so that these functions can be chained.

        Examples
        --------
        A repeating script only pinging an API if no cache was found::

            import os
            from fail_safe import FailSafeState, LocalStorage, storage

            api_data = None

            state = (
                FailSafeState()
                .uses(LocalStorage())
                .attach("api_data")
                .when_complete(storage.RETAIN)
            )

            # If we manually instruct a data reset, then we do so before the context.
            if os.environ.get("RESET_API_DATA") == "1":
                state.wipe()

            with state:
                if not api_data:
                    api_data = some_expensive_api_call()

            # You can now use `api_data` here; subsequent executions would not trigger
            # `some_expensive_api_call` again.
        """
        self.delete_cache = delete_cache

        return self
