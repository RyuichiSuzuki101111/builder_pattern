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


class builder_meta(type):  # pylint: disable=invalid-name
    """
    The builder_meta metaclass is responsible for initializing build_executor_factories and
    process_executor_factories dictionaries and updating them with the build_step and process_step
    attributes found in the Builder subclass.
    """

    def __init__(cls,
                 __name: str,
                 __bases: tuple[type, ...],
                 __namespace: dict[str, Any]):
        cls.build_executor_factories: dict[Any, ExecutorFactory] = {}
        cls.process_executor_factories: dict[Any, ExecutorFactory] = {}

        default_process_executor_factory: Any = None

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, process_step):
                if attr.default:
                    if default_process_executor_factory is not None:
                        raise ValueError('A subclass of Builder is allowed '
                                         'to have only one default process step.')
                    default_process_executor_factory = attr.executor_factory

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, (build_step, process_step)):
                # pylint: disable=no-value-for-parameter
                cls.update_map(cast(Any, attr))

        if default_process_executor_factory is not None:
            for step_key in cls.build_executor_factories:
                cls.process_executor_factories.setdefault(
                    step_key, default_process_executor_factory)

    def update_map(cls, step: build_step[Any] | process_step[Any]) -> None:
        """
        Update the build_executor_factories or process_executor_factories
        dictionary with the given step.
        """

        match step:
            case build_step():
                executor_factories = cls.build_executor_factories
            case process_step():
                executor_factories = cls.process_executor_factories

        for step_key in step.step_keys:

            if step_key in executor_factories:
                raise ValueError(f'Step key "{step_key}" is already in use by another step. '
                                 'Please use a unique step key for each step.')

            executor_factories[step_key] = step.executor_factory


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

    def build(self) -> FinalProduct:
        """
        This function builds the final product of this class.
        The processes in this function consist of the following steps:

        - Initialize the state for build process using the overridden create_initial_state method.
        - Iterate through build and process steps. A pair of build and process steps
          consists of freely defined operations associated with a step key.
          Build steps create intermediate products, while process steps
          modify the state based on the intermediate products.
        - Evaluate the resulting state and generate the final product using
          the overridden evaluate_final_state method.
        """
        state = self.create_initial_state()

        build_executor_factories = type(self).build_executor_factories
        process_executor_factories = type(self).process_executor_factories

        for step_key in self._filtered_and_sorted_process_step_keys():

            build_executor = build_executor_factories[step_key](self)
            intermediate_product = build_executor(step_key)

            process_executor = process_executor_factories[step_key](self)
            state = process_executor(intermediate_product, state, step_key)

        return self.evaluate_final_state(state)

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

    def create_initial_state(self) -> State:
        """
        Create the initial state for the building process.
        Subclasses should override this method to return a custom initial state.
        """
        raise NotImplementedError()

    def evaluate_final_state(self, state: State) -> FinalProduct:
        """
        Evaluate the final state and return the built object.
        Subclasses should override this method to return a
        custom built object based on the final state.
        """
        raise NotImplementedError()

    def _unfiltered_process_step_keys(self) -> list[StepKey]:
        return list(type(self).process_executor_factories.keys())

    def _filtered_and_sorted_process_step_keys(self) -> list[StepKey]:
        return self.filter_and_sort_process_step_keys(self._unfiltered_process_step_keys())
