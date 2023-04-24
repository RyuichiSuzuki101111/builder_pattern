"""
step.py

This module provides the base step class and its derivatives, build_step and process_step.
These classes serve as a foundation for defining a series of steps in a builder pattern.
"""

import inspect
from typing import Any, Callable, Self, TypeVar, Generic, cast

StepKey = TypeVar('StepKey')


class _step(Generic[StepKey]):
    """
    Base class for custom descriptor classes that wrap functions with a step_key.
    """

    step_keys: list[StepKey]
    func: Callable[..., Any]

    def __call__(self, func: Callable[..., Any]) -> Self:
        """
        This method is called when the descriptor is used as a decorator.
        If another _step instance is passed as an argument, their step_keys are combined.
        """

        if isinstance(func, _step):
            _func = cast(Self, func)
            _func.step_keys.extend(self.step_keys)
            return _func

        self.func = func
        return self

    @property
    def _name(self) -> str:
        return self.func.__name__

    def __get__(self, instance: Any, owner: Any) -> Callable[..., Any]:

        if instance is None:
            return self

        return self.func

    def executor_factory(self, builder: Any) -> Callable[..., Any]:
        """
        This method should be implemented by the subclasses to return an appropriate executor.
        """
        raise NotImplementedError()


class build_step(_step[StepKey]):  # pylint: disable=invalid-name,too-few-public-methods
    """
    Descriptor class for build steps.
    Inherits from the _step class and modifies the __get__ method to return
    a callable that doesn't take any arguments.

    The wrapped function should have either of the following signature:

    def func_name(self) -> IntermediateProduct:\n
        ...

    def func_name(self, step_key: StepKey) -> IntermediateProduct:\n
        ...

    All the type variables in these signatures are associated with
    a concrete subclass of Builder, where this descriptor is used.

    """

    def __init__(self, *step_key: StepKey):
        self.step_keys: list[StepKey] = list(step_key)

    def executor_factory(self, builder: Any):

        def executor(step_key: StepKey) -> Any:

            sig = inspect.signature(self.func)

            if len(sig.parameters) == 1:
                return self.func(builder)

            if len(sig.parameters) == 2:
                return self.func(builder, step_key)

            raise ValueError("Unexpected number of parameters in the function signature.")

        return executor


class process_step(_step[StepKey]):  # pylint: disable=invalid-name,too-few-public-methods
    """
    Descriptor class for process steps.
    Inherits from the _step class without changing its behavior.

    The wrapped function should have either of the following signature:

    def func_name(self,\n
                  intermediate_product: IntermediateProduct,\n
                  state: State) -> State:\n
        ...

    def func_name(self,\n
                  intermediate_product: IntermediateProduct,\n
                  state: State,\n
                  step_key: StepKey) -> State:\n
        ...

    All the type variables in these signatures are associated with
    a concrete subclass of Builder, where this descriptor is used.

    The 'default' attribute can be set to True for a single process step in a Builder subclass.
    This will make the process step the default process step for all build steps that do not have
    a specific process step defined.

    Args:
        *step_keys (StepKey): One or more step keys associated with this process step.
        default (bool): Optional, whether this process step should be used as the default
                        process step for all build steps. Defaults to False.
    """

    def __init__(self, *step_keys: StepKey, default: bool = False):
        self.step_keys = list(step_keys)
        self.default: bool = default

    def executor_factory(self, builder: Any):

        def executor(intermediate_product: Any,
                     state: Any,
                     step_key: StepKey) -> Any:

            sig = inspect.signature(self.func)

            if len(sig.parameters) == 3:
                return self.func(builder,
                                 intermediate_product,
                                 state)

            if len(sig.parameters) == 4:
                return self.func(builder,
                                 intermediate_product,
                                 state,
                                 step_key)

            raise ValueError("Unexpected number of parameters in the function signature.")

        return executor
