from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from src.exceptions import (
    GuardException,
    TransitionNotFoundException,
    WrongStateException,
)


class State: ...


class StateAwareContext:
    """
    Context that has a state attribute.
    """

    state: str


T = TypeVar("T", bound="StateAwareContext")


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


class Transition(metaclass=ABCMeta):
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
    def transition_guards(self) -> list["TransitionGuard"]:
        return []

    @property
    def before_callbacks(self) -> list["TransitionCallback"]:
        return []

    @property
    def after_callbacks(self) -> list["TransitionCallback"]:
        return []


class TransitionGuard(Generic[T], metaclass=ABCMeta):
    """
    Function that performs a check on the context to determine if a transition is allowed.
    """

    @abstractmethod
    def __call__(self, context: T) -> bool: ...


class TransitionCallback:
    """
    Callback function to be attached to a transition.
    """

    @abstractmethod
    def __call__(self, context: T) -> None: ...


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
            guard(context)

        for callback in transition.before_callbacks:
            callback(context)

        context.state = transition.to_state

        for callback in transition.after_callbacks:
            callback(context)
