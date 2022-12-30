# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, Type, Union

from ..utils import frames
from . import storage


class FailSafeState:
    """
    Context manager that caches local scope upon exceptions; loads for next execution.
    """

    name: str

    attached: List[Any]
    state_stores: List[storage.StateStorage]

    def __init__(
        self,
        name: str = None,
        *,
        attach: List[str] = None,
        uses: List[storage.StateStorage] = None,
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

    def __enter__(self) -> "FailSafeState":
        self._entered = True

        _loaded_state = self.load_state()

        if isinstance(_loaded_state, dict):
            frames.set_caller_locals(**_loaded_state)

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_instance: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> bool:
        self._entered = False

        if isinstance(exc_type, type) and isinstance(exc_instance, BaseException):
            _suspend_state = self.filter_vars(frames.get_caller_locals())

            self.save_state(_suspend_state)
        else:
            self.del_state()

        return False

    def attach(self, *args: str) -> "FailSafeState":
        """
        Attach variables by :class:`str` name into the state.
        """
        for arg in args:
            if arg not in self.attached:
                self.attached.append(arg)

        return self

    def detach(self, *args: str) -> "FailSafeState":
        """
        Detach variables by :class:`str` name from the state.
        """
        for arg in args:
            if arg in self.attached:
                self.attached.remove(arg)

        return self

    def uses(self, *storages: storage.StateStorage) -> "FailSafeState":
        """
        Adds storages to this instance.
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
        """
        return {key: value for key, value in locals.items() if key in self.attached}

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Attempt to load a state from storage.
        """
        for store in self.state_stores:
            _loaded_state = store.load(self.name)

            if _loaded_state is not None:
                return _loaded_state

        return None

    def save_state(self, state: Dict[str, Any]):
        """
        Save a state to storage.
        """
        with ThreadPoolExecutor() as executor:
            for _ in executor.map(
                lambda store: store.save(self.name, state), self.state_stores
            ):
                pass

    def del_state(self):
        """
        Remove all states from storage.
        """
        with ThreadPoolExecutor() as executor:
            for _ in executor.map(
                lambda store: store.wipe(self.name), self.state_stores
            ):
                pass
