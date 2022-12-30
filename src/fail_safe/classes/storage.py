# -*- coding: utf-8 -*-
import abc
import random
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from uuid import uuid1

import dill as pickle


class StateStorage(abc.ABC):
    """
    Abstract base class for a state storage unit.
    """

    @abc.abstractmethod
    def load_data(self, name: str) -> bytes:
        """
        Load the pickled bytes.
        """

    @abc.abstractmethod
    def save_data(self, name: str, data: bytes):
        """
        Save the pickled bytes.
        """

    @abc.abstractmethod
    def wipe(self, name: str):
        """
        Remove any saved states.
        """

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a state from storage.

        Returns
        -------
        Dict[str, Any]
            If found; otherwise

        None
            If not found, or pickling error occured.
        """
        _data = self.load_data(name)

        if _data:
            try:
                return pickle.loads(_data)
            except pickle.UnpicklingError as e:
                pass

        return None

    def save(self, name: str, state: Dict[str, Any]):
        """
        Save a state to storage.

        Parameters
        ----------
        kwargs
            Variables to be saved.
        """
        try:
            _data = pickle.dumps(state)
        except pickle.PickleError as e:
            raise e from None

        self.save_data(name, _data)


class LocalStorage(StateStorage):
    """
    Load and Save states to the local disk.
    """

    path: Path

    def __init__(self, path: Union[Path, str]):
        self.path = self._prepare_path(path)

    @staticmethod
    def _prepare_path(path: Optional[Union[Path, str]]) -> Path:
        # path init
        if path is None:
            path = Path(".")
        elif isinstance(path, list):
            path = Path(*path)
        elif isinstance(path, dict):
            path = Path(**path)
        elif not isinstance(path, Path):
            path = Path(str(path))

        return path

    def _resolve_path(self, name: str) -> Path:
        path = self.path

        if not path.is_dir():
            raise OSError(f"`path` must be a directory; {str(path.resolve())} found.")

        path /= name

        path: str = (
            str(path)
            .format(
                now=datetime.now(),
                utcnow=datetime.utcnow(),
                today=date.today(),
                dir=Path().resolve().parent.name,
                rand="%04x" % random.randint(0, 65536),
                uuid=uuid1(),
            )
            .replace(" ", "_")
        )

        if not path.endswith(".pickle"):
            path += ".pickle"

        return Path(path).resolve()

    def load_data(self, name: str) -> bytes:
        path = self._resolve_path(name)

        if path.is_file():
            return path.read_bytes()

        return None

    def save_data(self, name: str, data: bytes):
        path = self._resolve_path(name)

        path.write_bytes(data)

    def wipe(self, name: str):
        path = self._resolve_path(name)

        if path.is_file():
            path.unlink()


# class S3Storage(StateStorage):
#     pass
