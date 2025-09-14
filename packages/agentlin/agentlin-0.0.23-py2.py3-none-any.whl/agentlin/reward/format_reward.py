from typing import Union

from agentlin.core.types import ContentData
from agentlin.reward.base import compute_binary_reward, compute_binary_reward_of_messages
from agentlin.reward.grade_think_format import validate_think_format, validate_think_answer_format


compute_format_reward = compute_binary_reward
compute_format_reward_of_messages = compute_binary_reward_of_messages


def compute_think_format_reward(content: Union[str, list[ContentData]]) -> float:
    return compute_format_reward(content, validate_think_format)


def compute_think_format_reward_of_messages(messages: list[ContentData]) -> float:
    return compute_format_reward_of_messages(messages, validate_think_format)


def compute_think_answer_format_reward(content: Union[str, list[ContentData]]) -> float:
    return compute_format_reward(content, validate_think_answer_format)


def compute_think_answer_format_of_messages(messages: list[ContentData]) -> float:
    return compute_format_reward_of_messages(messages, validate_think_answer_format)
