"""
step.py

This module provides the base step class and its derivatives, build_step and process_step.
These classes serve as a foundation for defining a series of steps in a builder pattern.
"""

from typing import Any, Callable, Self


class _step:
    """
    Base class for custom descriptor classes that wrap functions with a step_key.
    """

    def __init__(self, step_key: int):
        self._ordinal = step_key
        self._func: Callable[..., Any]

    def __call__(self, func: Callable[..., Any]) -> Self:
        self._func = func
        return self

    @property
    def _name(self) -> str:
        return self._func.__name__

    def __get__(self, instance: Any, owner: Any) -> Any:

        if instance is None:
            return self

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._func(instance, *args, **kwargs)

        return wrapper

