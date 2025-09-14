from typing import Annotated, Optional
import json

import typer
import asyncio
from loguru import logger

from agentlin.route.agent_config import load_agent_config
from agentlin.evaluation.core import load_evaluator

app = typer.Typer()


@app.command()
def run(
    name: Annotated[str, typer.Option(help="Environment or Evaluator name (plugin id)")],
    agent: Annotated[str, typer.Option(help="Path to the agent config directory or file")],
    eval_args: Annotated[Optional[str], typer.Option(help="JSON string of arguments passed to the evaluator loader")] = None,
    num_examples: Annotated[int, typer.Option(help="Limit number of examples (-1 for all)")] = -1,
    rollout_n: Annotated[int, typer.Option(help="Number of rollouts per example")] = 1,
    rollout_dir: Annotated[Optional[str], typer.Option(help="Directory to save rollouts")] = None,
    max_workers: Annotated[int, typer.Option(help="Max parallel workers (-1 auto)")] = -1,
):
    """Run an evaluation by evaluator name.

    Examples:

    $ agent-eval --name gsm8k --agent ./path/to/agent/main.md --eval-args '{"split": "test"}'
    """
    # Parse eval args
    if not eval_args:
        eval_args = "{}"
    try:
        eval_args_dict: dict = json.loads(eval_args)
    except Exception as e:
        logger.error(f"Invalid eval_args JSON: {e}")
        eval_args_dict: dict = {}

    # Prepare agent config
    agent_config = asyncio.run(load_agent_config(agent))

    evaluator_obj = load_evaluator(name, **eval_args_dict)
    if evaluator_obj is None:
        logger.error("No evaluator specified or failed to load evaluator.")
        return

    # Let evaluator decide dataset and strategy
    if hasattr(evaluator_obj, "async_evaluate") and callable(evaluator_obj.async_evaluate):
        return asyncio.run(
            evaluator_obj.async_evaluate(
                agent_config=agent_config,
                num_examples=num_examples,
                rollout_n_per_example=rollout_n,
                rollout_save_dir=rollout_dir,
                max_workers=max_workers,
            )
        )
    elif hasattr(evaluator_obj, "evaluate") and callable(evaluator_obj.evaluate):
        return evaluator_obj.evaluate(
            agent_config=agent_config,
            num_examples=num_examples,
            rollout_n_per_example=rollout_n,
            rollout_save_dir=rollout_dir,
            max_workers=max_workers,
        )
    else:
        raise RuntimeError("Evaluator does not expose evaluate/async_evaluate")


if __name__ == "__main__":
    app()
