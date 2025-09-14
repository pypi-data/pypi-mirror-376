from typing import Any, Optional
from pydantic import BaseModel

from xlin import append_to_json_list, load_json_list

from agentlin.core.types import DialogData, ToolData


class AgentStep(BaseModel):
    url: str
    input_messages: list[DialogData]
    output_messages: list[DialogData]
    inference_args: dict[str, Any] = {}
    tools: list[ToolData] = []
    is_answer: bool = False
    turn: int
    step: Optional[int]
    meta: dict[str, Any] = {}


class Trajectory(BaseModel):
    steps: list[AgentStep] = []

    def add_step(self, step: AgentStep):
        self.steps.append(step)

    def save_to_jsonl(self, filename: str):
        data = [step.model_dump() for step in self.steps]
        append_to_json_list(data, filename)

    @classmethod
    def from_jsonl(cls, filename: str) -> "Trajectory":
        data = load_json_list(filename)
        steps = [AgentStep.model_validate(item) for item in data]
        return cls(steps=steps)

