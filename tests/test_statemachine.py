from dataclasses import dataclass
from enum import StrEnum
from sre_parse import State

import pytest

from src.exceptions import GuardException
from src.statemachine import (
    StateAwareContext,
    StateGuard,
    StateMachine,
    Transition,
    TransitionCallback,
    TransitionGuard,
)


class MyStates(StrEnum):
    STARTED = "started"
    ENDED = "ended"


class MyTransition(StrEnum):
    END = "end"


@dataclass
class Process(StateAwareContext):
    state = MyStates.STARTED
    progress: int = 100


class MyEndTransitionBeforeCallback(TransitionCallback[Process]):
    async def __call__(self, context: Process) -> None:
        print("Trying to end process")


class MyEndTransitionAfterCallback(TransitionCallback[Process]):
    async def __call__(self, context: Process) -> None:
        print("Process ended")


class MyEndTransitionGuard(TransitionGuard[Process]):
    async def __call__(self, context: Process) -> bool:
        return context.progress == 100


class MyEndTransition(Transition[Process]):
    @property
    def from_states(self) -> list[str]:
        return [MyStates.STARTED]

    @property
    def to_state(self) -> str:
        return MyStates.ENDED

    @property
    def transition_guards(self) -> list[TransitionGuard[Process]]:
        return [MyEndTransitionGuard()]

    @property
    def before_callbacks(self) -> list[TransitionCallback[Process]]:
        return [MyEndTransitionBeforeCallback()]

    @property
    def after_callbacks(self) -> list[TransitionCallback[Process]]:
        return [MyEndTransitionAfterCallback()]


class MyStateMachine(StateMachine[Process]):
    @property
    def transitions(self) -> dict[str, Transition[Process]]:
        return {MyTransition.END: MyEndTransition()}


@pytest.mark.anyio
async def test_statemachine_end_transition() -> None:
    process = Process()
    state_machine = MyStateMachine()

    await state_machine.transition(process, MyTransition.END)
    assert process.state == MyStates.ENDED
    assert process.progress == 100


@pytest.mark.anyio
async def test_statemachine_end_transition_with_uncompleted_process() -> None:
    process = Process(progress=50)
    state_machine = MyStateMachine()
    assert process.progress == 50

    with pytest.raises(GuardException):
        await state_machine.transition(process, MyTransition.END)
    assert process.state == MyStates.STARTED
    assert process.progress == 50
