# -*- coding: utf-8 -*-
"""
=========================
 Environment Definitions
=========================
Environment settings, mostly relating to a temporary non-production state e.g.
``pytest`` or ``sphinx`` build.
"""
import os
from typing import Any, Callable


def get(key: str, modifier: Callable[[str], Any], *, default: Any = None) -> Any:
    """
    Fetch an environment variable, then run it through the modifier.

    Typically he modifier is to change its type, e.g. :class:`int`, :class:`bool` etc.

    Parameters
    ----------
    key : str
        The environment variable name to get.

    modifier : Callable[[str], Any]
        A Callable to transform the found value. Useful for type coersion, since
        environment variables are always stored as :class:`str`.

        .. note::
            If ``modifier`` is ``bool``, special cases apply:

            - Any case-insensitive string value ``"true"`` is considered ``True``.
            - Any case-insensitive string value ``"false"`` is considered ``False``.
            - String values containing only ``0-9`` numerics, then the number is
              converted to :class:`int` before applying :class:`bool`.

    default : Any
        The default value if not found, or modifier encountered an :class:`Exception`.

    Returns
    -------
    Any
        The resultant value.
    """
    _value = os.environ.get(key, default=default)

    if modifier is bool:

        def modifier(value: str) -> bool:
            """
            Special bool transform.
            """
            value = value.strip()

            if value.lower() == "true":
                return True

            if value.lower() == "false":
                return False

            if value.isnumeric():
                return bool(int(value))

            return bool(value)

    try:
        return modifier(_value)
    except Exception as e:
        return default


PYTEST_IS_RUNNING = get("PYTEST_RUNNING", False, default=False)
"""
``True`` if pytest is running, otherwise ``False``.

Set Environment Variable ``PYTEST_RUNNING`` to change this value manually.
"""

SPHINX_IS_BUILDING = get("SPHINX_BUILD", False, default=False)
"""
``True`` value if sphinx is building, otherwise ``False``.

Set Environment Variable ``SPHINX_BUILD`` to change this value manually.
"""
