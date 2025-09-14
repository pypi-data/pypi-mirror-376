from typing import Callable, Optional, Union

from loguru import logger

from agentlin.core.types import ContentData, DialogData


TYPE_REWARD_FUNC = Callable[[Union[str, list[ContentData]]], float]


def compute_binary_reward(content: Union[str, list[ContentData]], binary_validate: Callable[[str], bool]) -> float:
    if isinstance(content, str):
        return 1.0 if binary_validate(content) else 0.0
    elif isinstance(content, list):
        texts = []
        for item in content:
            if "text" in item:
                texts.append(item["text"])
        if texts:
            combined_text = "\n".join(texts)
            return 1.0 if binary_validate(combined_text) else 0.0
        else:
            return 0.0
    return 0.0


def compute_binary_reward_of_messages(messages: list[DialogData], binary_validate: Callable[[str], bool]) -> float:
    scores: list[float] = []
    for msg in messages:
        if msg["role"] == "assistant":
            content = msg["content"]
            score = compute_binary_reward(content, binary_validate)
            scores.append(score)

    return sum(scores) / len(scores) if scores else 0.0


def composable_reward_of_content(content: Union[str, list[ContentData]], reward_functions: list[TYPE_REWARD_FUNC], reducer: Optional[Callable[[list[float]], float]] = None) -> float:
    scores = []
    for func in reward_functions:
        reward = func(content)
        scores.append(reward)
    if reducer:
        return reducer(scores)
    return sum(scores) if scores else 0.0


def composable_reward_of_messages(messages: list[DialogData], reward_functions: list[TYPE_REWARD_FUNC], reducer: Optional[Callable[[list[float]], float]] = None) -> float:
    scores = []
    for msg in messages:
        if msg["role"] == "assistant":
            content = msg["content"]
            reward = composable_reward_of_content(content, reward_functions, reducer)
            scores.append(reward)
    if scores:
        return reducer(scores) if reducer else sum(scores) / len(scores)
    return 0.0


def weight_reduced(scores: list[float], weights: list[float]) -> float:
    if len(scores) != len(weights):
        logger.warning("Length of scores and weights do not match.")
        return sum(scores) / len(scores) if scores else 0.0
    weighted_sum = sum(r * w for r, w in zip(scores, weights))
    total_weight = sum(weights)
    return weighted_sum / total_weight if total_weight != 0 else 0.0


def weighted_composable_reward_of_content(content: Union[str, list[ContentData]], weight_reward_functions: list[tuple[float, TYPE_REWARD_FUNC]]) -> float:
    reward = 0.0
    for weight, func in weight_reward_functions:
        reward += weight * func(content)
    return reward

def weighted_composable_reward_of_messages(messages: list[DialogData], weight_reward_functions: list[tuple[float, TYPE_REWARD_FUNC]]) -> float:
    reward = 0.0
    for msg in messages:
        if msg["role"] == "assistant":
            content = msg["content"]
            reward += weighted_composable_reward_of_content(content, weight_reward_functions)
    return reward
