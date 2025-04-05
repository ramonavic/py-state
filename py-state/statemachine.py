from abc import ABCMeta, abstractmethod
from typing import Generic, TypeAlias, TypeVar

from src.exceptions import (
    GuardException,
    TransitionNotFoundException,
    WrongStateException,
)

State: TypeAlias = str


class StateAwareContext:
    """
    Context that has a state attribute.
    """

    state: State


T = TypeVar("T", bound="StateAwareContext")


class Transition(Generic[T], metaclass=ABCMeta):
    """
    Base class to define a transition from one state to another.
    """

    @property
    @abstractmethod
    def from_states(self) -> list[State]: ...

    @property
    @abstractmethod
    def to_state(self) -> State: ...

    @property
    def transition_guards(self) -> list["TransitionGuard[T]"]:
        return []

    @property
    def before_callbacks(self) -> list["TransitionCallback[T]"]:
        return []

    @property
    def after_callbacks(self) -> list["TransitionCallback[T]"]:
        return []


class TransitionGuard(Generic[T], metaclass=ABCMeta):
    """
    Function that performs a check on the context to determine if a transition is allowed.
    """

    @abstractmethod
    async def __call__(self, context: T) -> bool: ...


class TransitionCallback(Generic[T], metaclass=ABCMeta):
    """
    Callback function to be attached to a transition.
    """

    @abstractmethod
    async def __call__(self, context: T) -> None: ...


class StateMachine(Generic[T], metaclass=ABCMeta):
    """
    Base class for a state machine.
    """

    @property
    @abstractmethod
    def transitions(self) -> dict[str, Transition[T]]: ...

    async def transition(self, context: T, transition_name: str) -> None:
        transition = self.transitions.get(transition_name)
        if transition is None:
            raise TransitionNotFoundException(transition_name)

        if context.state not in transition.from_states:
            raise WrongStateException()

        for guard in transition.transition_guards:
            if not await guard(context):
                raise GuardException()

        for callback in transition.before_callbacks:
            await callback(context)

        context.state = transition.to_state

        for callback in transition.after_callbacks:
            await callback(context)


class StateGuard(Generic[T], metaclass=ABCMeta):
    _allowed_states: list[State]
    """
    Check if context is one of the allowed states before executing an action.
    """

    def __init__(self, allowed_states: list[State]):
        self._allowed_states = allowed_states

    def __call__(self, context: T) -> None:
        if context.state not in self._allowed_states:
            raise GuardException(f"Action not allowed in state {context.state}")
