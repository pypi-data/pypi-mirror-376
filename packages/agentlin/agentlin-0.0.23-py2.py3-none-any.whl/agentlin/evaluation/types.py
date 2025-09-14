from typing import Optional, Type, Any, Callable, TypedDict


class RolloutInput(TypedDict):
    id: str
    example: dict[str, Any]

    task_args: Optional[dict[str, Any]]


class RolloutResult(TypedDict):
    id: str
    example: dict[str, Any]
    rollouts: list[dict[str, Any]]

    task_args: Optional[dict[str, Any]]


class ScoreResult(TypedDict):
    id: str
    example: dict[str, Any]
    rollouts: list[dict[str, Any]]
    scores: list[dict[str, float]]
    avg_score: float

    task_args: Optional[dict[str, Any]]


class EvaluationResult(TypedDict):
    evaluator: str
    avg_score: float
    rollout_with_scores: list[ScoreResult]
