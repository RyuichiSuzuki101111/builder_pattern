"""
builder.py

This module provides the generic Builder class and its associated metaclass builder_meta.
The Builder class is designed to construct a product using a sequence of build and process steps.

The Builder class is parameterized by the following type variables:
- FinalProduct: The type of the product being constructed.
- IntermediateProduct: The type of the parts of the final product being constructed.
- State: The type of the intermediate state used during the building process.
- StepKey: The type of the keys used to identify build and process steps.

Subclasses of Builder should override the following methods:
- create_initial_state: Create the initial state for the building process.
- evaluate_final_state: Evaluate the final state and return the built object.

Optionally, subclasses can also override the filter_and_sort_process_step_keys method
to change the order of process steps or exclude certain steps from the building process.

The builder_meta metaclass is responsible for initializing build_executor_creators and
process_executor_creators dictionaries and updating them with the build_step and process_step
attributes found in the Builder subclass.
"""

from typing import Any, Callable, Generic, TypeVar, cast
from .step import build_step, process_step, StepKey

IntermediateProduct = TypeVar('IntermediateProduct')
FinalProduct = TypeVar('FinalProduct')
State = TypeVar('State')
ExecutorFactory = Callable[['Builder[Any, Any, Any, Any]'], Callable[..., Any]]


# pylint: disable=invalid-name
class builder_meta(type):
    """
    The builder_meta metaclass is responsible for initializing build_executor_creators and
    process_executor_creators dictionaries and updating them with the build_step and process_step
    attributes found in the Builder subclass.
    """

    def __init__(cls,
                 __name: str,
                 __bases: tuple[type, ...],
                 __namespace: dict[str, Any]):
        cls.build_executor_factories: dict[Any, ExecutorFactory]
        cls.process_executor_factories: dict[Any, ExecutorFactory]

        for attr_name in dir(cls):

            attr = getattr(cls, attr_name)

            if isinstance(attr, (build_step, process_step)):
                # pylint: disable=no-value-for-parameter
                cls.update_map(cast(Any, attr))

    def update_map(cls, step: build_step[Any] | process_step[Any]) -> None:
        """
        Update the build_executor_creators or process_executor_creators dictionary
        with the given step.
        """

        match step:
            case build_step():
                factories = cls.build_executor_factories
            case process_step():
                factories = cls.build_executor_factories

        for step_key in step.step_keys:

            if step_key in factories:
                raise ValueError(f'Step key "{step_key}" is already in use by another step. '
                                 'Please use a unique step key for each step.')

            factories[step_key] = step.executor_factory


class Builder(Generic[FinalProduct, IntermediateProduct, State, StepKey], metaclass=builder_meta):
    """
    A generic Builder class that constructs a Product using a sequence of build and process steps.

    The Builder class is parameterized by the following type variables:
    - FinalProduct: The type of the final product being constructed.
    - IntermediateProduct: The type of the parts of the final product being constructed.
    - State: The type of the intermediate state used during the building process.
    - StepKey: The type of the keys used to identify build and process steps.

    Subclasses should override the following methods:

    - create_initial_state: Create the initial state for the building process.
    - evaluate_final_state: Evaluate the final state and return the built object.

    Optionally, subclasses can also override the filter_and_sort_process_step_keys method
    to change the order of process steps or exclude certain steps from the building process.
    """

    def filter_and_sort_process_step_keys(self,
                                          process_step_keys: list[StepKey]) -> list[StepKey]:
        """
        Filter and sort the process_step_keys based on custom criteria.

        This method is not mandatory to override, but it is recommended to do so
        in order to apply custom filtering and sorting logic to the process_step_keys.

        By default, this method returns the received process_step_keys without any modification.

        Args:
            process_step_keys (list[StepKey]): List of step keys for filtering and sorting.

        Returns:
            list[StepKey]: The filtered and sorted list of process step keys.
        """
        return process_step_keys

    def _unfiltered_process_step_keys(self) -> list[StepKey]:
        return list(type(self).process_executor_factories.keys())

    def _filtered_and_sorted_process_step_keys(self) -> list[StepKey]:
        return self.filter_and_sort_process_step_keys(self._unfiltered_process_step_keys())
