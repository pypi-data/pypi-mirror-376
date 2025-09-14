from agentlin.environment.interface import IEnvironment, IStoppableState, IState
from agentlin.environment.state.text_state import ErrorState


class ComposedState(IStoppableState):
    def __init__(self, name2state: dict[str, IState]):
        self.name2state = name2state

    def check_validity(self) -> bool:
        return all(state.check_validity() for state in self.name2state.values())

    def display(self):
        messages = []
        block_list = []
        done = True
        for name, state in self.name2state.items():
            state_display = state.display()
            state_messages = state_display.get("message_content", [])
            if len(state_messages) == 0:
                state_messages = [{"type": "text", "text": "[No displayable content]"}]
            messages.append({"type": "text", "text": f"=== {name} ==="})
            messages.extend(state_messages)
            block_list.append({"type": "text", "text": f"=== {name} ==="})
            block_list.extend(state_display.get("block_list", []))
            if isinstance(state, IStoppableState):
                done = done and state.done
        return {
            "message_content": messages,
            "block_list": block_list,
            "data": {"done": done},
        }


class ComposedEnvironment(IEnvironment):
    """An environment that composes multiple environments sequentially."""

    def __init__(self, name2environment: dict[str, IEnvironment]):
        super().__init__()
        self.name2environment = name2environment

    def forward(self, s: ComposedState, **kwargs) -> ComposedState:
        if s.done:
            return s
        if not s.check_validity():
            return ErrorState("The composed state is invalid.", done=True)
        name2next_state = {}
        for name, env in self.name2environment.items():
            if name not in s.name2state:
                next_state = ErrorState(f"State for environment '{name}' not found in the composed state.", done=True)
            else:
                current_state = s.name2state[name]
                action = kwargs.get(name, {})
                next_state = env(current_state, **action)
            name2next_state[name] = next_state
        return ComposedState(name2next_state)

    def provide_initial_state(self) -> ComposedState:
        name2initial_state = {}
        for name, env in self.name2environment.items():
            name2initial_state[name] = env.provide_initial_state()
        return ComposedState(name2initial_state)


def compose_named_envs(name2environment: dict[str, IEnvironment]) -> ComposedEnvironment:
    return ComposedEnvironment(name2environment)
