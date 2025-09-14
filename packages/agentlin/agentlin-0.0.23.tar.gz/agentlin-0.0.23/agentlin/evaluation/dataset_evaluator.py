from typing import Any, Awaitable, Callable, Literal, Optional, TypedDict, Union

from datasets import Dataset
from agentlin.evaluation.interface import IEvaluator
from agentlin.evaluation.types import EvaluationResult, RolloutInput, RolloutResult, ScoreResult
from agentlin.route.agent_config import AgentConfig


class DatasetEvaluator(IEvaluator):
    def __init__(
        self,
        name: str,
        dataset: Dataset,
        eval_dataset: Dataset,
        rollout_func: Union[
            Callable[[RolloutInput], RolloutResult],
            Callable[[list[RolloutInput]], list[RolloutResult]],
            Callable[[RolloutInput], Awaitable[RolloutResult]],
            Callable[[list[RolloutInput]], Awaitable[list[RolloutResult]]],
        ],
        reward_func: Union[
            Callable[[RolloutResult], ScoreResult],
            Callable[[list[RolloutResult]], list[ScoreResult]],
            Callable[[RolloutResult], Awaitable[ScoreResult]],
            Callable[[list[RolloutResult]], Awaitable[list[ScoreResult]]],
        ],
        is_batch_rollout_func: bool = False,
        is_batch_reward_func: bool = False,
    ):
        self.name = name
        self.dataset = dataset
        self.eval_dataset = eval_dataset
        self.rollout_func = rollout_func
        self.reward_func = reward_func
        self.is_batch_rollout_func = is_batch_rollout_func
        self.is_batch_reward_func = is_batch_reward_func

    async def async_evaluate(
        self,
        agent_config: AgentConfig,
        split: Literal["train", "test"] = "test",
        rollout_n_per_example: int = 1,
        rollout_save_dir: Optional[str] = None,
        num_examples: int = -1,
        max_workers: int = -1,
        cache_path: Optional[str] = None,
        **kwargs,
    ) -> EvaluationResult:
        from agentlin.evaluation.core import dataset_rollout_agent, score_rollouts

        if split == "test":
            inputs = self.eval_dataset
        else:
            inputs = self.dataset

        results = await dataset_rollout_agent(
            inputs=inputs,
            agent_config=agent_config,
            rollout_func=self.rollout_func,
            rollout_n_per_example=rollout_n_per_example,
            rollout_save_dir=rollout_save_dir,
            num_examples=num_examples,
            is_batch_rollout_func=self.is_batch_rollout_func,
            max_workers=max_workers,
            cache_path=cache_path,
            **kwargs,
        )

        scores = await score_rollouts(
            results,
            score_func=self.reward_func,
            is_batch_score_func=self.is_batch_reward_func,
            max_workers=max_workers,
            **kwargs,
        )
        avg_score = sum(r["avg_score"] for r in scores) / len(scores) if scores else 0.0
        return EvaluationResult(
            evaluator=self.name,
            avg_score=avg_score,
            rollout_with_scores=scores,
        )
