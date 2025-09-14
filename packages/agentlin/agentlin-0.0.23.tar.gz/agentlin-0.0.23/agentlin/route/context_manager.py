from loguru import logger
from typing_extensions import Literal, Union, TypedDict, TypeAlias, Required, Optional
from pydantic import BaseModel
from openai.types.responses.response_input_param import (
    EasyInputMessageParam,
    ResponseOutputMessageParam,
    ResponseFunctionToolCallParam,
    FunctionCallOutput,
    ResponseReasoningItemParam,
)

from agentlin.core.types import BlockData, ContentData, ResponsesContentData
from agentlin.core.agent_schema import remove_thoughts_in_messages, responses_content_to_completion_content


class ContextInputMessage(EasyInputMessageParam):
    message_content: Optional[list[ContentData]]
    block_list: Optional[list[BlockData]]
    # 我们可能拿 user message 来作为某一个工具调用的 function call output 的一部分，以使得工具结果支持多模态。
    # 需要记录一下 call_id，知道这个 message 属于哪一次工具调用
    call_id: Optional[str] = None


class ContextOutputMessage(ResponseOutputMessageParam):
    message_content: Optional[list[ContentData]]
    block_list: Optional[list[BlockData]]
    response_id: Optional[str] = None
    compact_id: Optional[str] = None


class ContextToolCall(ResponseFunctionToolCallParam):
    pass


class ContextToolCallOutput(FunctionCallOutput):
    pass


class ContextReasoningItem(ResponseReasoningItemParam):
    pass


ContextData: TypeAlias = Union[
    ContextInputMessage,
    ContextOutputMessage,
    ContextToolCall,
    ContextToolCallOutput,
    ContextReasoningItem,
]

# [q, a, q, a]
HistoryMessage: TypeAlias = Union[
    ContextInputMessage,
    ContextOutputMessage,
]

# [reasoning, tool_call, tool_call_output, reasoning]
ThoughtMessage: TypeAlias = Union[
    ContextReasoningItem,
    ContextToolCall,
    ContextToolCallOutput,
    ContextInputMessage,
]



def responses_messages_to_context_messages(responses_messages: list[ResponsesContentData]) -> list[ContextData]:
    """
    Convert response messages to context messages.
    主要是带上 message_content 和 block_list
    """
    context_messages: list[ContextData] = []
    for response_message in responses_messages:
        message_content = []
        block_list = []
        if isinstance(response_message, EasyInputMessageParam):
            content = response_message.get("content", [])
            if content:
                if isinstance(content, str):
                    content = responses_content_to_completion_content(content)
                    message_content.append(content)
                    block_list.append(content)
                elif isinstance(content, list):
                    content = [responses_content_to_completion_content(item) for item in content]
                    message_content.extend(content)
                    block_list.extend(content)
                else:
                    logger.warning(f"Unexpected content type: {type(content)}")
            context_message = ContextInputMessage(
                **response_message,
                message_content=message_content,
                block_list=block_list,
            )
        elif isinstance(response_message, ResponseOutputMessageParam):
            content = response_message.get("content", [])
            if content:
                if isinstance(content, str):
                    content = responses_content_to_completion_content(content)
                    message_content.append(content)
                    block_list.append(content)
                elif isinstance(content, list):
                    content = [responses_content_to_completion_content(item) for item in content]
                    message_content.extend(content)
                    block_list.extend(content)
                else:
                    logger.warning(f"Unexpected content type: {type(content)}")
            context_message = ContextOutputMessage(
                **response_message,
                message_content=message_content,
                block_list=block_list,
            )
        elif isinstance(response_message, ContextToolCall):
            context_message = ContextToolCall(response_message)
        elif isinstance(response_message, ContextToolCallOutput):
            context_message = ContextToolCallOutput(response_message)
        elif isinstance(response_message, ContextReasoningItem):
            context_message = ContextReasoningItem(response_message)
        context_messages.append(context_message)
    return context_messages


class ContextManager:
    """
    Manage the context of the conversation.
    """

    # [SYS]
    # [SYS, q, a]
    # [SYS, q, a, q, a]
    # [SYS, DEV]
    # [SYS, DEV, q, a]
    # [SYS, DEV, q, a, q, a]
    history_messages: list[ContextData]

    # q w/ system-reminders
    user_message: ContextData

    # [reasoning, output_text]
    # [reasoning, function_call, function_call_output, reasoning, output_text]
    # [reasoning, function_call, function_call_output w/ system-reminders, reasoning, output_text]
    thought_messages: list[ContextData]

    # 压缩
    # [SYS, q, a, q, a, human_msg] -> [reasoning, tool_call] : total_tokens > 0.9 * max_model_length
    # [SYS_compact, q, a, q, a, human_msg, reasoning, tool_call, fake_function_call_output, compact_prompt] -> compact_output
    # [SYS, compact_output] -> [reasoning, tool_call, ...]
    # 也就是把 [SYS, q, a, q, a, human_msg] 压缩为了 [SYS, compact_output]

    def __init__(self):
        self.history_messages = []
        self.user_message = ContextData(message_content=[], block_list=[])
        self.thought_messages = []

    def context_messages(self):
        history_messages = remove_thoughts_in_messages(self.history_messages, inplace=False)
        context_messages = history_messages + [self.user_message] + self.thought_messages
        return context_messages
