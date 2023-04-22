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


class build_step(_step):
    """
    Descriptor class for build steps.
    Inherits from the _step class and modifies the __get__ method to return
    a callable that doesn't take any arguments.
    """

    def __get__(self, instance: Any, owner: Any) -> Any:

        if instance is None:
            return self

        def wrapper() -> Any:
            return self._func(instance)

        return wrapper


class process_step(_step):
    """
    Descriptor class for process steps.
    Inherits from the _step class without changing its behavior.
    """
