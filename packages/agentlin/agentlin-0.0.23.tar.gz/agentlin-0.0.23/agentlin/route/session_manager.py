import asyncio
from collections import defaultdict
import os
from pathlib import Path
import time
from typing import Type, TypedDict
from typing_extensions import Any, AsyncIterable
import json
import uuid
from fastmcp import Client as MCPClient
from loguru import logger
import copy
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion import ChatCompletion

from xlin import append_to_json_list, load_text
from agentlin.code_interpreter.types import ToolResponse
from agentlin.core.multimodal import is_text_content
from agentlin.core.types import *
from agentlin.core.agent_schema import (
    content_to_text,
    extract_apply,
    extract_apply_block,
    extract_code,
    extract_thought,
    parse_function_call_response,
    parse_text_with_apply,
    remove_citations_in_messages,
    remove_thoughts,
    messages_to_text,
    create_logger,
    remove_thoughts_in_messages,
)
from agentlin.core.usage import Usage
from agentlin.route.agent_config import SubAgentConfig, AgentConfig, CodeInterpreterConfig, get_agent_id, get_agent_config
from agentlin.route.context_manager import ContextData, ContextInputMessage
from agentlin.route.memory_manager import UserStore
from agentlin.route.reference_manager import ReferenceManager
from agentlin.route.task_manager import InMemoryTaskManager, merge_streams
from agentlin.route.tool_task_manager import ToolTaskManager
from agentlin.route.code_task_manager import CodeTaskManager, ExecuteRequest
from agentlin.route.model_task_manager import ModelTaskManager
from agentlin.tools.builtin.file_system_tools import MemoryTool, TodoWriteTool
from agentlin.tools.tool_calendar import format_datetime_with_holiday
from agentlin.tools.tool_todo import todo_read


class SessionState(BaseModel):
    session_id: str
    user_id: str
    host_frontend_id: str
    main_agent_id: str
    host_code_kernel_id: Optional[str] = None
    agent_config: AgentConfig
    env: Optional[dict[str, str]] = None

    # 短期记忆
    history_messages: list[DialogData] = []
    thought_messages: list[DialogData] = []
    # dialog_id2references: dict[str, ReferenceManager] = {}  # 引用池, 用于溯源。会话级别
    registered_tools: list[ToolData] = []  # 已注册的工具列表
    usage: Usage = Field(default_factory=Usage)

    # 运行时 - 这些属性不参与 BaseModel 的序列化和验证
    model_config = {"arbitrary_types_allowed": True, "extra": "allow"}

    def __init__(self, **data):
        # 提取运行时管理器，避免传入 BaseModel 验证
        model_task_manager = data.pop("model_task_manager", None)
        tool_task_manager = data.pop("tool_task_manager", None)
        code_task_manager = data.pop("code_task_manager", None)

        # 先调用父类的 __init__
        super().__init__(**data)

        # 然后设置运行时属性
        self.model_task_manager: ModelTaskManager = model_task_manager
        self.tool_task_manager: ToolTaskManager = tool_task_manager
        self.code_task_manager: CodeTaskManager = code_task_manager

    def get_subagent_by_name(self, name: str) -> Optional[SubAgentConfig]:
        for subagent in self.agent_config.builtin_subagents:
            if subagent.name == name:
                return subagent
        return None

    def get_subagents(self, allowed_subagents: Optional[list[str]] = None) -> list[SubAgentConfig]:
        if allowed_subagents is None:
            return self.agent_config.builtin_subagents
        filtered_subagents = []
        for subagent in self.agent_config.builtin_subagents:
            if subagent.name in allowed_subagents:
                filtered_subagents.append(subagent)
        return filtered_subagents

    def get_tools(self, allowed_tools: Optional[list[str]] = None) -> list[ToolData]:
        if allowed_tools is None:
            return self.agent_config.builtin_tools
        filtered_tools = []
        for tool in self.agent_config.builtin_tools:
            if tool["name"] in allowed_tools:
                filtered_tools.append(tool)
        return filtered_tools

    def apply_env_change(self, env: Optional[dict[str, str]]):
        if not env:
            return
        diff = {k: v for k, v in env.items() if k not in self.env or self.env[k] != v}
        if len(diff) == 0:
            return
        self.env.update(env)
        # apply to agent
        for key, value in diff.items():
            self.agent_config.developer_prompt = self.agent_config.developer_prompt.replace("{{" + key + "}}", str(value))
            if self.agent_config.code_for_agent:
                self.agent_config.code_for_agent = self.agent_config.code_for_agent.replace("{{" + key + "}}", str(value))
            if self.agent_config.code_for_interpreter:
                self.agent_config.code_for_interpreter = self.agent_config.code_for_interpreter.replace("{{" + key + "}}", str(value))
        # apply to subagent
        for subagent in self.agent_config.builtin_subagents:
            for key, value in diff.items():
                subagent.developer_prompt = subagent.developer_prompt.replace("{{" + key + "}}", str(value))
                if subagent.code_for_agent:
                    subagent.code_for_agent = subagent.code_for_agent.replace("{{" + key + "}}", str(value))
                if subagent.code_for_interpreter:
                    subagent.code_for_interpreter = subagent.code_for_interpreter.replace("{{" + key + "}}", str(value))
        # apply to manager
        self.tool_task_manager.apply_env_change(diff)

    async def start(self):
        self.tool_task = None
        if self.tool_task_manager:
            await self.tool_task_manager.initialize()
            self.tool_task = asyncio.create_task(self.tool_task_manager.run())

    def stop(self):
        if self.code_task_manager:
            kernel_id = self.host_code_kernel_id
            if kernel_id:
                self.code_task_manager.delete_kernel(kernel_id)
        if self.tool_task_manager:
            self.tool_task_manager.stop()
            if self.tool_task:
                if self.tool_task.done():
                    self.tool_task = None
                else:
                    logger.warning(f"Failed to stop tool task for session {self.session_id}")


class SessionRequest(BaseModel):
    user_id: str
    host_frontend_id: str
    user_message_content: list[ContentData]
    user_block_list: Optional[list[BlockData]] = None

    key: Optional[str] = None
    agent_config: Optional[AgentConfig] = None
    allowed_tools: Optional[list[str]] = None  # 允许的工具列表. None 为允许所有，[] 为不允许任何
    disallowed_tools: Optional[list[str]] = None  # 不允许的工具列表. None 和 [] 不进行处理
    allowed_subagents: Optional[list[str]] = None  # 允许的子代理列表. None 为允许所有，[] 为不允许任何
    stop_tools: Optional[list[str]] = None  # 遇到 stop_tools 时终止. None 和 [] 不进行处理
    client_tools: Optional[list[ToolData]] = None  # 客户端的工具定义，遇到客户端工具时一定终止，等用户执行完客户端工具后再在下一个请求中继续执行。客户端工具都是 stop_tools。

    # agent 级的 completion 模式：
    # 存在 history_messages 或 thought_messages 非空时，不清空驻留在内存中的 thought_messages 栈，
    # 而是将传进来的 history_messages 或 thought_messages 拼到末尾，继续 agent 循环
    history_messages: list[dict] = []
    thought_messages: list[dict] = []

    # agent 的环境
    target_directory: Optional[str] = None  # 当前工作目录, 用于 file_system_mcp 和代码解释器
    env: Optional[dict[str, str]] = None  # 环境变量

    # 推理参数
    inference_args: Optional[dict[str, Any]] = None

    # 输出
    structured_output: Optional[Type[BaseModel]] = None

    # 运行模式
    # 下面 3 个模式都会以文件形式存储 LLM 的轨迹数据，区别在于流式数据返回的内容
    # 1. online_deployment: 线上部署，流式返回渲染信号，而不返回 LLM 的轨迹数据，供测试或者客户端使用。
    # 2. online_rollout: 线上采样，流式返回 rollout 的 LLM 的轨迹数据（rollout 过程中能即时拿到中间结果）
    # 3. offline_rollout: 离线采样，流式返回任务状态信号（开始、结束或者失败），不返回 LLM 的轨迹数据
    mode: Literal["online_deployment", "online_rollout", "offline_rollout"] = "online_deployment"
    rollout_save_dir: Optional[str] = None


class ExecuteSubAgentRequest(BaseModel):
    name: str
    description: str
    prompt: str


class SessionTaskManager(InMemoryTaskManager):
    def __init__(
        self,
        debug=False,
        use_message_queue=False,
        user_file: Optional[str] = None,
    ):
        """Initialize the session task manager.

        Args:
            debug (bool, optional): Enable debug mode. Defaults to False.
            use_message_queue (bool, optional): Use message queue for task management. Defaults to False.
            user_file (str, optional): Path to the user file. Defaults to None.
        """
        super().__init__()
        self.sessions: dict[str, SessionState] = {}
        self.debug = debug
        self.use_message_queue = use_message_queue
        self.user_store = UserStore()
        if user_file:
            self.user_store.load_from_file(user_file)

    def build_system_content(self, session_id: str, session_state: SessionState) -> str:
        developer_prompt = session_state.agent_config.developer_prompt
        user_id = session_state.user_id
        user_data = self.user_store.get_user(user_id)
        user_profile = user_data.user_profile if user_data else ""
        code_for_agent = session_state.agent_config.code_for_agent

        developer_prompt = developer_prompt.replace("{{code_functions}}", code_for_agent)
        developer_prompt = developer_prompt.replace("{{all_user_profile}}", user_profile)
        env = session_state.env
        if env:
            for key, value in env.items():
                developer_prompt = developer_prompt.replace("{{" + key + "}}", str(value))

        system_content = [
            {"type": "text", "text": developer_prompt},
        ]
        return system_content

    def query_nlu(self, query: str):
        # 这里可以调用 NLU 服务进行查询
        return ""

    def build_system_code_for_interpreter(self, session_id: str, session_state: SessionState) -> str:
        code_mcp_config = session_state.agent_config.code_mcp_config
        code_for_interpreter = session_state.agent_config.code_for_interpreter
        code = code_for_interpreter
        code = code.replace("{{code_mcp_config}}", json.dumps(code_mcp_config, ensure_ascii=False))
        code = code.replace("{{session_id}}", session_id)
        code = code.replace("{{main_agent_id}}", session_state.main_agent_id)
        code = code.replace("{{host_frontend_id}}", session_state.host_frontend_id)
        env = session_state.env
        if env:
            for key, value in env.items():
                code = code.replace("{{" + key + "}}", str(value))
        if self.debug:
            logger.debug(f"Total system code for session {session_id}:\n{code}")
        return code

    async def lazy_init_kernel(self, session_id: str, session_state: SessionState) -> str:
        kernel_id = session_state.host_code_kernel_id
        if kernel_id:
            return kernel_id
        code_task_manager = session_state.code_task_manager
        kernel_id = code_task_manager.create_kernel()
        session_state.host_code_kernel_id = kernel_id
        code = self.build_system_code_for_interpreter(session_id, session_state)
        await self.execute_code(session_id, kernel_id, code, code_task_manager)
        return kernel_id

    async def execute_code(self, session_id: str, kernel_id: str, code: str, code_task_manager: CodeTaskManager):
        req = ExecuteRequest(
            kernel_id=kernel_id,
            code=code,
            mode="full",
        )
        request = SendTaskRequest(
            params=TaskSendParams(
                sessionId=session_id,
                payload=req.model_dump(),
            )
        )
        resp = await code_task_manager.on_send_task(request)
        if resp.error:
            logger.error(f"Failed to execute code: {resp.error}")
            return
        task_result = resp.result
        if not task_result:
            logger.error(f"Failed to execute code: no result")
            return
        code_result: ToolResponse = task_result.metadata
        if not code_result:
            logger.error(f"Failed to execute code: no metadata")
            return
        return code_result

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        host_frontend_id: str,
        agent_config: Optional[AgentConfig] = None,
        target_directory: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ) -> SessionState:
        if agent_config is None:
            main_agent_id = await get_agent_id(host_frontend_id)
            agent_config = await get_agent_config(main_agent_id, env=env)
        main_agent_id = agent_config.agent_id

        model = agent_config.model
        agent_config.inference_args.setdefault("max_tokens", 10 * 1024)  # 设置默认最大 token 数量
        agent_config.inference_args.setdefault("model", model)  # 设置默认模型
        model_task_manager = ModelTaskManager(
            agent_id=main_agent_id,
        )
        tool_mcp_config = agent_config.tool_mcp_config
        # tool_mcp_client = MCPClient(tool_mcp_config)
        # async with tool_mcp_client:
        #     tools = await tool_mcp_client.list_tools()
        tool_task_manager = ToolTaskManager(
            host_frontend_id=host_frontend_id,
            agent_id=main_agent_id,
            mcp_config=tool_mcp_config,
            target_directory=target_directory,
            env=env,
        )
        await tool_task_manager.discover_tools()
        registered_tools = await tool_task_manager.get_tools()
        logger.debug(f"Registered tools for {main_agent_id}: {', '.join(tool['function']['name'] for tool in registered_tools)}")

        code_interpreter_config = agent_config.code_interpreter_config
        if not code_interpreter_config:
            raise ValueError("Code interpreter configuration is required for CodeTaskManager.")
        code_task_manager = CodeTaskManager(
            agent_id=main_agent_id,
            jupyter_host=code_interpreter_config.jupyter_host,
            jupyter_port=code_interpreter_config.jupyter_port,
            jupyter_token=code_interpreter_config.jupyter_token,
            jupyter_timeout=code_interpreter_config.jupyter_timeout,
            jupyter_username=code_interpreter_config.jupyter_username,
        )
        usage = Usage()
        state = SessionState(
            session_id=session_id,
            user_id=user_id,
            host_frontend_id=host_frontend_id,
            main_agent_id=main_agent_id,
            host_code_kernel_id=None,
            agent_config=agent_config,
            tool_task_manager=tool_task_manager,
            code_task_manager=code_task_manager,
            model_task_manager=model_task_manager,
            registered_tools=registered_tools,
            env=env,
            usage=usage,
        )
        if self.use_message_queue:
            await state.start()
        self.sessions[session_id] = state
        return state

    def get_session(self, session_id: str):
        return self.sessions.get(session_id, None)

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            session_state = self.sessions[session_id]
            if self.use_message_queue:
                session_state.stop()
            del self.sessions[session_id]

    async def streaming_chat(
        self,
        user_message_content: list[ContentData],
        host_frontend_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        key: Optional[str] = None,
        agent_config: Optional[AgentConfig] = None,
        allowed_tools: Optional[list[str]] = None,
        disallowed_tools: Optional[list[str]] = None,
        allowed_subagents: Optional[list[str]] = None,
        stop_tools: Optional[list[str]] = None,
        client_tools: Optional[list[ToolData]] = None,
        history_messages: Optional[list[DialogData]] = None,
        thought_messages: Optional[list[DialogData]] = None,
        inference_args: Optional[dict[str, Any]] = None,
        target_directory: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        mode: Literal["online_deployment", "online_rollout", "offline_rollout"] = "online_deployment",
        rollout_save_dir: Optional[str] = None,
    ):
        """
        向 SessionTaskManager 发送一个任务请求，开始一个会话。
        Args:
            user_message_content: 用户消息内容
            host_frontend_id: 前端 ID, 可选 AInvest, iWencai 等
            trace_id: 跟踪 ID
            session_id: 会话 ID
            task_id: 任务 ID
            user_id: 用户 ID
            key: 消息键值
            agent_config: 主机代理配置
            allowed_tools: 允许的工具列表. None 为允许所有，[] 为不允许任何
            disallowed_tools: 不允许的工具列表. None 和 [] 不进行处理
            allowed_subagents: 允许的子代理列表. None 为允许所有，[] 为不允许任何
            stop_tools: 遇到 stop_tools 时终止. None 和 [] 不进行处理
            client_tools: 客户端工具列表
            inference_args: 推理参数
            target_directory: 当前工作目录, 用于 file_system_mcp 和代码解释器
            env: 环境变量
            structured_output: 结构化输出模型
            mode: 运行模式, online_deployment, online_rollout, offline_rollout
            rollout_save_dir: rollout 保存路径
        Returns:
            AsyncIterable[SendTaskStreamingResponse | JSONRPCResponse]: 任务流响应
        """
        trace_id = trace_id if trace_id else uuid.uuid4().hex
        task_id = task_id if task_id else uuid.uuid4().hex
        session_id = session_id if session_id else uuid.uuid4().hex
        user_id = user_id if user_id else uuid.uuid4().hex
        host_frontend_id = host_frontend_id if host_frontend_id else "AIME"
        history_messages = history_messages if history_messages is not None else []
        thought_messages = thought_messages if thought_messages is not None else []

        req = SessionRequest(
            user_id=user_id,
            host_frontend_id=host_frontend_id,
            user_message_content=user_message_content,
            key=key,
            agent_config=agent_config,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            allowed_subagents=allowed_subagents,
            stop_tools=stop_tools,
            client_tools=client_tools,
            history_messages=history_messages,
            thought_messages=thought_messages,
            inference_args=inference_args,
            target_directory=target_directory,
            env=env,
            structured_output=structured_output,
            mode=mode,
            rollout_save_dir=rollout_save_dir,
        )
        request = SendTaskStreamingRequest(
            id=trace_id,
            params=TaskSendParams(
                id=task_id,
                sessionId=session_id,
                payload=req.model_dump(),
            ),
        )
        return await self.on_send_task_subscribe(request)

    async def __call__(self,
        user_message_content: list[ContentData],
        host_frontend_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        key: Optional[str] = None,
        agent_config: Optional[AgentConfig] = None,
        allowed_tools: Optional[list[str]] = None,
        disallowed_tools: Optional[list[str]] = None,
        allowed_subagents: Optional[list[str]] = None,
        stop_tools: Optional[list[str]] = None,
        client_tools: Optional[list[ToolData]] = None,
        history_messages: Optional[list[DialogData]] = None,
        thought_messages: Optional[list[DialogData]] = None,
        inference_args: Optional[dict[str, Any]] = None,
        target_directory: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        mode: Literal["online_deployment", "online_rollout", "offline_rollout"] = "online_deployment",
        rollout_save_dir: Optional[str] = None,
    ):
        trace_id = trace_id if trace_id else uuid.uuid4().hex
        task_id = task_id if task_id else uuid.uuid4().hex
        session_id = session_id if session_id else uuid.uuid4().hex
        user_id = user_id if user_id else uuid.uuid4().hex
        host_frontend_id = host_frontend_id if host_frontend_id else "AIME"
        history_messages = history_messages if history_messages is not None else []
        thought_messages = thought_messages if thought_messages is not None else []

        req = SessionRequest(
            user_id=user_id,
            host_frontend_id=host_frontend_id,
            user_message_content=user_message_content,
            key=key,
            agent_config=agent_config,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            allowed_subagents=allowed_subagents,
            stop_tools=stop_tools,
            client_tools=client_tools,
            history_messages=history_messages,
            thought_messages=thought_messages,
            inference_args=inference_args,
            target_directory=target_directory,
            env=env,
            structured_output=structured_output,
            mode=mode,
            rollout_save_dir=rollout_save_dir,
        )
        request = SendTaskRequest(
            id=trace_id,
            params=TaskSendParams(
                id=task_id,
                sessionId=session_id,
                payload=req.model_dump(),
            ),
        )
        response = await self.on_send_task(request)
        return response

    async def structured_output(self, request: SendTaskRequest) -> BaseModel:
        req = self._validate_request(request)
        if isinstance(req, JSONRPCError):
            raise ValueError(f"Invalid request: {req}")
        if req.structured_output is None:
            raise ValueError("structured_output is required for structured output request")
        subscribe_request = SendTaskStreamingRequest(
            id=request.id,
            params=request.params,
        )
        stream = await self.on_send_task_subscribe(subscribe_request)
        async for response in stream:
            # 处理流响应
            if isinstance(response, SendTaskStreamingResponse):
                result = response.result
                if isinstance(result, TaskArtifactUpdateEvent):
                    # 处理任务结果更新事件
                    if result.metadata:
                        if "structured_output" in result.metadata:
                            return result.metadata["structured_output"]
        raise ValueError("No structured output found in the response")

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        req = self._validate_request(request)
        if isinstance(req, JSONRPCError):
            return SendTaskResponse(id=request.id, error=req)
        subscribe_request = SendTaskStreamingRequest(
            id=request.id,
            params=request.params,
        )
        stream = await self.on_send_task_subscribe(subscribe_request)
        message_content = []
        block_list = []
        async for response in stream:
            # 处理流响应
            if isinstance(response, SendTaskStreamingResponse):
                result = response.result
                if isinstance(result, TaskArtifactUpdateEvent):
                    # 处理任务结果更新事件
                    if result.metadata:
                        if req.mode == "online_rollout":
                            data = result.metadata
                            if "type" in data and data["type"] == "rollout":
                                block_list.append(data)
                        else:
                            message_content.append(result.metadata.get("message_content", []))
                            block_list.extend(result.metadata.get("block_list", []))
        # 最终返回一个完整的任务响应
        return SendTaskResponse(
            id=request.id,
            result=TaskArtifactUpdateEvent(
                id=request.params.id,
                metadata={
                    "message_content": message_content,
                    "block_list": block_list,
                },
            ),
        )

    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse]:
        await self.upsert_task(request.params)
        task_send_params: TaskSendParams = request.params
        request_id = request.id
        task_id = task_send_params.id
        session_id = task_send_params.sessionId
        return self._stream_generator(request, session_id, request_id, task_id)

    async def _stream_generator(
        self,
        request: SendTaskStreamingRequest,
        session_id: str,
        request_id: str,
        task_id: str,
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        # 响应优化，立即接受任务
        resp = await self.working_streaming_response(request_id=request_id, task_id=task_id)
        yield resp

        # 安全检测
        req = self._validate_request(request)
        if isinstance(req, JSONRPCError):
            logger.error(f"Error in tool task: {req}")
            resp = await self.fail_streaming_response(request_id=request_id, task_id=task_id, error=req)
            yield resp
            return

        # 开始处理任务

        # 获得上下文
        user_id = req.user_id
        host_frontend_id = req.host_frontend_id
        user_message_content = req.user_message_content
        key = req.key or f"msg_{uuid.uuid4().hex}"

        session_state = self.get_session(session_id)
        if session_state:
            logger.debug("recover session_state")
        if session_state is None or req.agent_config is not None:
            # 新的 session，或者新的 agent，都需要重新开一个 session
            session_state = await self.create_session(
                session_id,
                user_id,
                host_frontend_id,
                agent_config=req.agent_config,
                target_directory=req.target_directory,
                env=req.env,
            )

        response_usage = Usage()
        model_task_manager = session_state.model_task_manager
        tool_task_manager = session_state.tool_task_manager
        code_task_manager = session_state.code_task_manager
        history_messages = session_state.history_messages
        thought_messages = session_state.thought_messages

        if req.target_directory and req.target_directory != tool_task_manager.target_directory:
            tool_task_manager.target_directory = req.target_directory
            await tool_task_manager.discover_tools()
            session_state.registered_tools = await tool_task_manager.get_tools()

        # 确认 tools 有哪些
        builtin_tools = session_state.agent_config.get_builtin_tools(req.allowed_subagents)  # core builtin tools: CodeInterpreter, Task
        registered_tools = session_state.registered_tools  # builtin tools + mcp tools
        client_tools = req.client_tools or []
        total_tools: list[ToolData] = builtin_tools + registered_tools + client_tools

        stop_tools = req.stop_tools or []
        for tool in client_tools:
            stop_tools.append(tool.get("function", {}).get("name"))
        if req.structured_output is not None:
            # 如果指定了结构化输出，则添加结构化输出工具
            structured_output_tool_name = "GenerateStructuredOutput"
            tool_schema = req.structured_output.model_json_schema()
            if "title" in tool_schema:
                tool_schema["title"] = structured_output_tool_name
            if "name" in tool_schema:
                tool_schema["name"] = structured_output_tool_name
            total_tools.append(
                {
                    "type": "function",
                    "function": tool_schema,
                }
            )
            stop_tools.append(structured_output_tool_name)
        total_tool_names = [tool.get("function", {}).get("name") for tool in total_tools]
        tools = copy.deepcopy(total_tools)  # 深拷贝，避免修改原始工具列表
        if req.allowed_tools and "*" not in req.allowed_tools:
            tools = [tool for tool in tools if tool.get("function", {}).get("name") in req.allowed_tools]
        if req.disallowed_tools and len(req.disallowed_tools) > 0:
            tools = [tool for tool in tools if tool.get("function", {}).get("name") not in req.disallowed_tools]
        tool_names = [tool.get("function", {}).get("name") for tool in tools]
        allowed_name2tool: dict[str, BaseTool] = {}
        for tool in tools:
            tool_name = tool.get("function", {}).get("name")
            tool_obj = tool_task_manager.get_tool(tool_name)
            if tool_obj:
                allowed_name2tool[tool_name] = tool_obj
        if len(tools) != len(total_tools):
            # 有一些工具被过滤掉了
            logger.warning(f"allowed tools: [{', '.join(tool_names)}]")
            logger.warning(f"disallowed tools: [{', '.join([tool_name for tool_name in total_tool_names if tool_name not in tool_names])}]")

        # 确认推理参数
        inference_args = dict()
        inference_args.update(session_state.agent_config.inference_args)
        if req.inference_args:
            inference_args.update(req.inference_args)
        inference_args["tools"] = tools

        # if self.debug:
        #     logger.debug(f"Session {session_id} inference_args: {json.dumps(inference_args, ensure_ascii=False, indent=2)}")

        # 初始化引用管理器
        reference_manager = ReferenceManager()
        # ? 在历史轮的答案里保留引用会影响效果吗？
        # ? 由于模型看到历史轮里的可引用数据和引用编号，导致模型输出的引用[^1]可能实际引用的是历史轮里的数据而不是当前轮的数据，从而产生冲突
        # ? 因此，多轮情况下，如果保留历史轮的引用，那当前轮的引用编号应该从上一轮最后一个引用编号+1 开始
        # ? 但是，这样复杂度会显著上升。而且模型引用历史轮里的数据有点奇怪，尤其是历史轮里的代码执行结果，可能变量已经被覆盖或者内核已经重置，在当前轮中并不存在
        # ? 所以，应该约束引用的使用范围，确保当前轮的引用只包含当前轮的有效数据。历史轮中的引用和引用编号都丢弃，只保留当前轮的引用。
        # ? 后续可引入动态裁剪工具，将没用的工具输出裁剪掉

        current_step = 0
        if len(thought_messages) > 0:
            current_step = sum([1 for m in thought_messages if m["role"] == "assistant"])

        if len(history_messages) == 0:
            system_content = self.build_system_content(session_id, session_state)
            history_messages.append({"role": "system", "content": system_content})

        if req.history_messages:
            history_messages.extend(req.history_messages)
        if req.thought_messages:
            thought_messages.extend(req.thought_messages)

        if not req.history_messages and not req.thought_messages:
            thought_messages.clear()
        else:
            logger.warning("接收到指定上下文，不清空思考过程，而是基于指定上下文继续思考")

        # 我们把跟用户对话时效性强相关的内容从 role=system 移动到 role=user 中，避免 system content 的缓存失效
        if user_message_content:
            is_first_turn = len([m for m in history_messages if m["role"] != "system"]) == 0
            new_user_message_content, new_user_block_list = await self.wrap_user_message_content(
                user_message_content,
                user_message_content,
                allowed_name2tool,
                is_first_turn,
                is_compact=False,
            )

            history_messages.append({"role": "user", "content": new_user_message_content})

        while True:
            current_step += 1
            if self.debug:
                logger.debug(f"历史消息数量: {len(history_messages)}, 当前推理深度: {current_step}")
            # 调用推理引擎获取回复
            # 只有之前轮里的 think 在 history_messages 里需要去掉，而当前轮的 think 在 thought_messages 里需要保留
            messages = remove_citations_in_messages(remove_thoughts_in_messages(history_messages)) + thought_messages
            if self.debug:
                logger.debug(messages_to_text([m for m in messages if m["role"] != "system"]))

            reasoning_content: str = ""
            tool_calls: list[ToolCallContentData] = []
            answer_content: str = ""
            # 先考虑把 tool_calls 整理出来。整理完可能是空列表。
            # "tool_calls": [
            #     {
            #         "function": {
            #             "arguments": "{}",
            #             "name": "Search"
            #         },
            #         "id": "call_g16uvNKM2r7L36PcHmgbPAAo",
            #         "type": "function"
            #     }
            # ]
            total_tokens = None

            model_request = await self.streaming_request(
                request_id=request_id,
                task_id=task_id,
                session_id=session_id,
                payload={
                    "messages": messages,
                    "inference_args": inference_args,
                },
            )
            stream = await model_task_manager.on_send_task_subscribe(model_request)
            async for chunk in stream:
                if isinstance(chunk, SendTaskStreamingResponse):
                    result = chunk.result
                    if isinstance(result, TaskStatusUpdateEvent):
                        final = result.final
                        if final:
                            logger.info(f"Task {result.id} completed with status: {result.status}")
                        else:
                            logger.info(f"Task {result.id} status updated: {result.status}")
                    elif isinstance(result, TaskArtifactUpdateEvent):
                        metadata = result.metadata
                        if metadata:
                            if "reasoning_content" in metadata["choices"][0]["delta"] and isinstance(metadata["choices"][0]["delta"]["reasoning_content"], str):
                                reasoning_content += metadata["choices"][0]["delta"]["reasoning_content"]
                                del metadata["choices"][0]["delta"]["reasoning_content"]
                            chunk = ChatCompletionChunk.model_validate(metadata)
                            if chunk.choices and len(chunk.choices) > 0:
                                choice = chunk.choices[0]
                                if choice.delta.tool_calls:
                                    for t in choice.delta.tool_calls:
                                        found = False
                                        for existing_t in tool_calls:
                                            if existing_t["id"] == t.id:
                                                found = True
                                                if t.function:
                                                    # 更新现有的 tool call
                                                    if t.function.arguments is not None:
                                                        existing_t["function"]["arguments"] += t.function.arguments
                                                    if t.function.name is not None:
                                                        existing_t["function"]["name"] += t.function.name
                                        if not found:
                                            if t.id is None:
                                                existing_t = tool_calls[-1]
                                                if t.function:
                                                    # 更新现有的 tool call
                                                    if t.function.arguments is not None:
                                                        existing_t["function"]["arguments"] += t.function.arguments
                                                    if t.function.name is not None:
                                                        existing_t["function"]["name"] += t.function.name
                                            else:
                                                tool_call: ToolCallContentData = {
                                                    "id": t.id,
                                                    "type": "function",
                                                    "function": {
                                                        "name": t.function.name if isinstance(t.function.name, str) else "",
                                                        "arguments": t.function.arguments if isinstance(t.function.arguments, str) else "",
                                                    },
                                                }
                                                tool_calls.append(tool_call)

                                    if choice.delta.content:
                                        reasoning_content += str(choice.delta.content)
                                elif choice.delta.content:
                                    answer_content += str(choice.delta.content)
                                if choice.finish_reason:
                                    # 处理完成原因
                                    pass
                            if chunk.usage:
                                usage = chunk.usage
                                # 处理使用情况
                                # 每多调用一次 LLM 都要累加 token 消耗
                                response_usage.add_completion_usage(usage)
                                session_state.usage.add_completion_usage(usage)
                                total_tokens = usage.total_tokens

                            # yield SendTaskStreamingResponse(
                            #     id=request_id,
                            #     result=TaskArtifactUpdateEvent(
                            #         id=task_id,
                            #         metadata={
                            #             "block_list": [chunk],
                            #             "current_step": current_step,
                            #             "key": f"{key}/model_msg_{current_step}",
                            #         },
                            #     ),
                            # )
                            # 只发射按 reasoning_content, answer_content 和 tool_calls 分类后的结果
            if self.debug:
                logger.debug(response_usage.model_dump_json(indent=2))
            if answer_content:
                thought = extract_thought(answer_content)
                if thought:
                    reasoning_content += f"<think>{thought}</think>"

                response_without_thoughts = remove_thoughts(answer_content)
                code = extract_code(response_without_thoughts)
                call_id = f"call_{uuid.uuid4().hex}"
                if code and len(code.strip()) > 0:
                    call_args = {
                        "code": code,
                    }
                    tool_call: ToolCallContentData = {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "arguments": json.dumps(call_args, ensure_ascii=False),
                            "name": "CodeInterpreter",
                        },
                    }
                    tool_calls.append(tool_call)
            if reasoning_content:
                # reasoning_content 的 think 标记可能有残缺，统一处理为完整的 think 标记
                reasoning_content = reasoning_content.strip("</think>").strip("<think>").strip()
                reasoning_content = f"<think>{reasoning_content}</think>"
                if req.mode == "online_deployment":
                    yield SendTaskStreamingResponse(
                        id=request_id,
                        result=TaskArtifactUpdateEvent(
                            id=task_id,
                            metadata={
                                "block_list": [{"type": "text", "text": reasoning_content}],
                                "current_step": current_step,
                                "key": f"{key}_assistant_thought_{current_step}",
                            },
                        ),
                    )
            if self.debug:
                debug_message = {"role": "assistant"}
                debug_content = []
                if reasoning_content:
                    debug_content.append({"type": "text", "text": reasoning_content})
                if answer_content:
                    debug_content.append({"type": "text", "text": answer_content})
                debug_message["content"] = debug_content
                if tool_calls:
                    debug_message["tool_calls"] = tool_calls
                logger.debug(f"{messages_to_text([debug_message])}")

            if tool_calls:
                if not reasoning_content and answer_content:
                    reasoning_content = answer_content
                tool_call_message = {"role": "assistant", "content": reasoning_content, "tool_calls": tool_calls}
                rollout = {
                    "type": "rollout",
                    "data": {
                        "input_messages": copy.deepcopy(messages),
                        "output_messages": copy.deepcopy([tool_call_message]),
                        "inference_args": copy.deepcopy(inference_args),
                        "request": req.model_dump(),
                        "is_answer": False,
                        "turn": len([m for m in history_messages if m["role"] == "assistant"]),
                        "step": current_step,
                    },
                }
                self.save_rollout(session_state, rollout, req.rollout_save_dir)
                if req.mode == "online_rollout":
                    yield SendTaskStreamingResponse(
                        id=request_id,
                        result=TaskArtifactUpdateEvent(
                            id=task_id,
                            metadata=rollout,
                        ),
                    )
                thought_messages.append(tool_call_message)
                # 上下文压缩分 2 个等级
                # 1.  0% token usage 触发：直接丢弃历史轮次中 reasoning（保留当前轮的 reasoning）
                # 2. 90% token usage 触发：将当前上下文提交给总结 agent 进行总结，然后清空历史轮和当前轮，用总结后的上下文继续思考
                if self.debug:
                    logger.debug(f"Token usage: {total_tokens}/{session_state.agent_config.max_model_length} ({total_tokens / session_state.agent_config.max_model_length:.2%})")
                if total_tokens is None:
                    logger.error("Total tokens is None, cannot check for context compression.")
                elif total_tokens > session_state.agent_config.compact_threshold_tokens:
                    # 处理超出最大模型长度的情况
                    # 将当前上下文提交给总结 agent 进行总结
                    compact_prompt = session_state.agent_config.compact_prompt
                    # 只有之前轮里的 think 在 history_messages 里需要去掉，而当前轮的 think 在 thought_messages 里需要保留
                    messages_to_compact = remove_citations_in_messages(remove_thoughts_in_messages(history_messages)) + thought_messages
                    compact_messages = self.build_compact_messages(compact_prompt, messages_to_compact)
                    compact_inference_args = {
                        "model": session_state.agent_config.compact_model,
                        "OPENAI_API_KEY": inference_args.get("OPENAI_API_KEY", None),
                        "OPENAI_BASE_URL": inference_args.get("OPENAI_BASE_URL", None),
                    }
                    payload = {
                        "messages": compact_messages,
                        "inference_args": compact_inference_args,
                    }
                    compact_request = await self.new_task_request(
                        request_id,
                        task_id=f"compact_{uuid.uuid4().hex}",
                        session_id=session_id,
                        payload=payload,
                    )
                    compact_response = await model_task_manager.on_send_task(compact_request)
                    if compact_response.error:
                        # 压缩出现错误
                        logger.error(f"Compact request failed: {compact_response.error}")
                        resp = await self.fail_streaming_response(request_id, task_id, compact_response.error)
                        yield resp
                        break
                    # 正常压缩上下文
                    compacted_result = compact_response.result
                    if not compacted_result:
                        error_message = "Compacted result is empty"
                        logger.error(error_message)
                        resp = await self.fail_streaming_response(request_id, task_id, error_message)
                        yield resp
                        break
                    # 处理压缩后的结果
                    compacted_completion: ChatCompletion = compacted_result.metadata
                    if compacted_completion.usage:
                        usage = compacted_completion.usage
                        # 处理使用情况
                        # 每多调用一次 LLM 都要累加 token 消耗
                        response_usage.add_completion_usage(usage)
                        session_state.usage.add_completion_usage(usage)
                    compacted_message = compacted_completion.choices[0].message
                    compacted_reasoning_content = ""
                    if hasattr(compacted_message, "reasoning_content"):
                        compacted_reasoning_content = compacted_message.reasoning_content
                    compacted_content = compacted_message.content
                    if not compacted_content:
                        error_message = "Compacted content is empty"
                        logger.error(error_message)
                        resp = await self.fail_streaming_response(request_id, task_id, error_message)
                        yield resp
                        break
                    # 保存一下模型调用的输入输出
                    rollout = {
                        "type": "rollout",
                        "data": {
                            "input_messages": copy.deepcopy(compact_messages),
                            "output_messages": [compacted_message.model_dump()],
                            "inference_args": copy.deepcopy(compact_inference_args),
                            "request": req.model_dump(),
                            "is_answer": False,
                            "is_compact": True,
                            "turn": len([m for m in history_messages if m["role"] == "assistant"]),
                            "step": current_step,
                        },
                    }
                    self.save_rollout(session_state, rollout, req.rollout_save_dir)
                    if req.mode == "online_rollout":
                        yield SendTaskStreamingResponse(
                            id=request_id,
                            result=TaskArtifactUpdateEvent(
                                id=task_id,
                                metadata=rollout,
                            ),
                        )
                    # 将当前用户的 query 改为压缩后的上下文
                    # 需要带上变量、文件路径
                    # TODO: 压缩的上下文里的引用[^1]如何处理？
                    kernel_id = await self.lazy_init_kernel(session_id, session_state)
                    compacted_message_content, compacted_block_list = await self.parse_answer(
                        session_id,
                        kernel_id,
                        compacted_content,
                        code_task_manager,
                        reference_manager,
                    )
                    prefix_content = []
                    prefix_content.append({"type": "text", "text": "This session is being continued from a previous conversation that ran out of context. The conversation is summarized below:"})
                    prefix_content.append({"type": "text", "text": "\nAnalysis:"})
                    prefix_content.append({"type": "text", "text": compacted_reasoning_content})
                    prefix_content.append({"type": "text", "text": "\nSummary:"})

                    # 处理 system-reminder、nlu、current_time 等边缘信息
                    # 第一轮需要带上 memory
                    is_first_turn = len([m for m in history_messages if m["role"] != "system"]) == 0
                    new_user_message_content, new_user_block_list = await self.wrap_user_message_content(
                        prefix_content + compacted_message_content,
                        prefix_content + compacted_block_list,
                        allowed_name2tool,
                        is_first_turn,
                        is_compact=True,
                    )
                    new_user_message = {"role": "user", "content": new_user_message_content}

                    # 清空上下文，替换为总结后的上下文
                    if len(history_messages) > 0 and history_messages[-1]["role"] == "user":
                        history_messages.pop(-1)
                    history_messages.append(new_user_message)
                    thought_messages.clear()
                    continue

                # 1. 开始执行
                call_id_to_name_args: dict[str, tuple[str, dict[str, Any]]] = {}
                block_list = []
                should_stop_tool_calls = False
                for tool_call in tool_calls:
                    call_id, call_name, call_args = parse_function_call_response(tool_call)
                    call_id_to_name_args[call_id] = (call_name, call_args)
                    block_list.append(
                        {
                            "type": "tool_call",
                            "data": {
                                "tool_name": call_name,
                                "tool_args": call_args,
                                "call_id": call_id,
                            },
                        }
                    )
                    if call_name in stop_tools:
                        should_stop_tool_calls = True
                        if call_name == structured_output_tool_name and req.structured_output is not None:
                            try:
                                structured_output_instance = req.structured_output.model_validate(call_args)
                            except Exception as e:
                                error_message = f"Failed to validate structured output: {e}"
                                logger.error(error_message)
                                resp = await self.fail_streaming_response(
                                    request_id=request_id,
                                    task_id=task_id,
                                    error=JSONRPCError(code=-32000, message=error_message),
                                )
                                yield resp
                                continue
                            yield SendTaskStreamingResponse(
                                id=request_id,
                                result=TaskArtifactUpdateEvent(
                                    id=task_id,
                                    metadata={
                                        "structured_output": structured_output_instance,
                                        "current_step": current_step,
                                        "key": f"{key}_assistant_msg_{current_step}",
                                    },
                                ),
                            )
                if req.mode == "online_deployment":
                    yield SendTaskStreamingResponse(
                        id=request_id,
                        result=TaskArtifactUpdateEvent(
                            id=task_id,
                            metadata={
                                "block_list": block_list,
                                "current_step": current_step,
                                "key": f"{key}_assistant_msg_{current_step}",
                            },
                        ),
                    )
                if should_stop_tool_calls:
                    # 如果遇到 stop_tools，则终止当前会话
                    logger.info(f"Session {session_id} stopped by tool call: {stop_tools}")
                    # 使用 break，使得 complete response 正常工作
                    break

                # 2. 执行
                call_response_streams = []  # 冷流。放进去的流只有定义，还未执行
                call_id_to_start_time: dict[str, float] = {}
                call_id_to_end_time: dict[str, float] = {}
                for call_id, (call_name, call_args) in call_id_to_name_args.items():
                    call_id_to_start_time[call_id] = time.time()
                    # builtin tools
                    if call_name == "Task":
                        # 3. 启动新的代理来处理复杂的多步骤任务
                        subagent_req = ExecuteSubAgentRequest.model_validate(call_args)
                        name = subagent_req.name
                        description = subagent_req.description
                        prompt = subagent_req.prompt
                        subagent = session_state.get_subagent_by_name(name)
                        if subagent is None:
                            error_message = f"Subagent '{name}' not found while calling Task."
                            logger.error(error_message)
                            resp = await self.tool_result_streaming_response(
                                request_id=request_id,
                                task_id=call_id,
                                message_content=[{"type": "text", "text": error_message}],
                                block_list=[],
                            )

                            async def agent_response() -> AsyncIterable[SendTaskStreamingResponse]:
                                yield resp

                            call_response_stream = agent_response()
                            continue
                        subagent_config = session_state.agent_config.model_copy()
                        subagent_config.name = subagent.name
                        subagent_config.description = subagent.description
                        if subagent.model:
                            subagent_config.model = subagent.model  # Optional model name
                        subagent_config.developer_prompt = subagent.developer_prompt
                        subagent_config.code_for_agent = subagent.code_for_agent
                        subagent_config.code_for_interpreter = subagent.code_for_interpreter
                        subagent_config.allowed_tools = subagent.allowed_tools
                        disallowed_tools = req.disallowed_tools or []
                        if "Task" not in disallowed_tools:
                            disallowed_tools.append("Task")  # 子代理不允许调用 Task 工具
                        if "Task" in subagent.allowed_tools:
                            subagent.allowed_tools.remove("Task")  # 从子代理允许的工具中移除 Task

                        task_req = SessionRequest(
                            user_id=user_id,
                            host_frontend_id=host_frontend_id,
                            user_message_content=[{"type": "text", "text": prompt}],
                            key=f"{key}_subagent_{name}_{current_step}",
                            agent_config=subagent_config,
                            allowed_tools=subagent.allowed_tools,  # 子代理允许的工具
                            disallowed_tools=disallowed_tools,  # 子代理不允许的工具
                            allowed_subagents=[],  # 子代理不允许其他子代理
                            stop_tools=[],  # 子代理不需要停止工具
                            client_tools=[],  # 子代理不需要客户端工具
                            history_messages=[],  # 子代理不需要历史消息
                            thought_messages=[],  # 子代理不需要思考过程
                            target_directory=req.target_directory,  # 子代理需要当前工作目录
                            env=session_state.env,  # 子代理需要环境变量
                            inference_args=None,  # 子代理不需要额外指定推理参数
                            structured_output=None,  # 子代理不需要结构化输出
                            # mode="subagent",  # 子代理只支持 subagent 模式，因为要对其返回结果进行解析和整理
                            rollout_save_dir=req.rollout_save_dir,
                        )
                        subagent_session_id = f"{session_id}_{name}_{uuid.uuid4().hex}"
                        task_request = SendTaskRequest(
                            id=request_id,
                            params=TaskSendParams(
                                id=call_id,
                                sessionId=subagent_session_id,  # 子代理使用全新的会话 ID，和当前会话隔离
                                payload=task_req.model_dump(),
                            ),
                        )
                        call_response_stream = await self.on_send_task_subscribe(task_request)
                    elif call_name == "CodeInterpreter":
                        code = call_args.get("code", "")
                        kernel_id = await self.lazy_init_kernel(session_id, session_state)

                        # 3. 执行代码
                        code_req = ExecuteRequest(kernel_id=kernel_id, code=code, mode="full", msg_id=call_id)
                        code_request = SendTaskStreamingRequest(
                            id=request_id,
                            params=TaskSendParams(
                                id=call_id,
                                sessionId=session_id,
                                payload=code_req.model_dump(),
                            ),
                        )
                        call_response_stream = await code_task_manager.on_send_task_subscribe(code_request)
                    else:
                        # 3. 执行工具调用
                        tool_request = SendTaskRequest(
                            id=request_id,
                            params=TaskSendParams(
                                id=call_id,
                                sessionId=session_id,
                                payload={
                                    "call_name": call_name,
                                    "call_args": call_args,
                                },
                            ),
                        )
                        call_response_stream = await tool_task_manager.on_send_task_subscribe(tool_request)
                    call_response_streams.append(call_response_stream)

                # 4. 处理执行结果, 处理引用
                call_id_to_result: dict[str, ToolResult] = defaultdict(lambda: ToolResult(message_content=[], block_list=[]))
                async for call_response in merge_streams(*call_response_streams):  # 冷流变“热“：开始正式执行。merge 表示多个流的异步并行合并
                    # if self.debug:
                    #     logger.debug(call_response)
                    if isinstance(call_response, SendTaskStreamingResponse):
                        result = call_response.result
                        if isinstance(result, TaskArtifactUpdateEvent):
                            metadata = result.metadata
                            call_id = result.id
                            call_id_to_end_time[call_id] = time.time()
                            if metadata:
                                # 要求：
                                # 1. 及时把 streaming response 返回给前端
                                # 2. 记录执行结果到上下文，按照 call_id 区分
                                metadata["current_step"] = current_step
                                call_name, call_args = call_id_to_name_args[call_id]
                                metadata["key"] = f"{key}_{call_name}_result@step_{current_step}"
                                metadata["call_id"] = call_id

                                message_content_delta = metadata.pop("message_content", [])
                                block_list_delta = metadata.pop("block_list", [])
                                tool_result = ToolResult(
                                    message_content=message_content_delta,
                                    block_list=block_list_delta,
                                )
                                new_tool_result = reference_manager.process_tool_result(tool_result)
                                call_id_to_result[call_id].extend_result(new_tool_result)
                                if self.debug:
                                    logger.debug(f"Tool call {call_id} result: {new_tool_result.model_dump_json(indent=2)}")
                                # metadata["message_content"] = new_tool_result.message_content  # 前端不需要 message_content
                                metadata["block_list"] = new_tool_result.block_list  # 前端需要 block_list, 这里的 block_list 已经附带真正的 reference number 了
                                metadata["message_content"] = new_tool_result.message_content

                                if len(metadata["block_list"]) > 0 and len(metadata["message_content"]) > 0:
                                    if req.mode == "online_deployment":
                                        yield SendTaskStreamingResponse(
                                            id=request_id,
                                            result=TaskArtifactUpdateEvent(
                                                id=task_id,
                                                metadata=metadata,
                                            ),
                                        )
                        elif isinstance(result, TaskStatusUpdateEvent):
                            # if self.debug:
                            # logger.debug(f"Received TaskStatusUpdateEvent: {result} for task {task_id}")
                            pass
                # 5. 记录工具调用结果到上下文
                if not call_id_to_result:
                    logger.warning(f"No tool call results for session {session_id}, current step {current_step}.")
                for call_id, result in call_id_to_result.items():
                    # if self.debug:
                    #     logger.debug(f"Tool call {call_id} result: {result.model_dump_json(indent=2)}")
                    message_content = result.message_content
                    call_name, _ = call_id_to_name_args[call_id]
                    if not message_content:
                        if call_name == "CodeInterpreter":
                            message_content = [{"type": "text", "text": "ok"}]

                    # 兼容一下 OpenAI 的 tool result 只能是 text 的情况
                    is_all_text = is_text_content(message_content)
                    if is_all_text:
                        thought_messages.append({"role": "tool", "content": message_content, "tool_call_id": call_id})
                    else:
                        thought_messages.append({"role": "tool", "content": [{"type": "text", "text": f"The execution results of {call_name} will be provided by the user as following:"}], "tool_call_id": call_id})
                        message_content.append({"type": "text", "text": f"The execution results of {call_name} are provided as above."})
                        thought_messages.append({"role": "user", "content": message_content})
                # 处理 call_id 匹配，当断流的时候没拿到 call_id 的结果时，可能会导致 call_id_to_result 为空，与 tool_calls 匹配不上
                for tool_call in tool_calls:
                    call_id, call_name, call_args = parse_function_call_response(tool_call)
                    start_time, end_time = call_id_to_start_time.get(call_id), call_id_to_end_time.get(call_id)
                    duration = end_time - start_time if start_time and end_time else None
                    response_usage.add_tool_call(call_id, time=duration)
                    session_state.usage.add_tool_call(call_id, time=duration)
                    if call_id not in call_id_to_result:
                        # 可能是断流，需要补上工具结果
                        if call_name == "CodeInterpreter":
                            thought_messages.append({"role": "tool", "content": [{"type": "text", "text": f"ok"}], "tool_call_id": call_id})
                        else:
                            thought_messages.append({"role": "tool", "content": [{"type": "text", "text": f"Tool call {call_name} with arguments '{str(call_args)[:20]}' did not return any result."}], "tool_call_id": call_id})
            else:
                # 没有调工具就是回答了
                reasoning_message_content = [{"type": "text", "text": reasoning_content}] if reasoning_content else []
                answer = remove_thoughts(answer_content)
                rollout = {
                    "type": "rollout",
                    "data": {
                        "input_messages": copy.deepcopy(messages),
                        "output_messages": copy.deepcopy([{"role": "assistant", "content": reasoning_message_content + [{"type": "text", "text": answer}]}]),
                        "inference_args": copy.deepcopy(inference_args),
                        "request": req.model_dump(),
                        "is_answer": True,
                        "turn": len([m for m in history_messages if m["role"] == "assistant"]),
                    },
                }
                self.save_rollout(session_state, rollout, req.rollout_save_dir)
                if req.mode == "online_rollout":
                    yield SendTaskStreamingResponse(
                        id=request_id,
                        result=TaskArtifactUpdateEvent(
                            id=task_id,
                            metadata=rollout,
                        ),
                    )
                answer_message_content, answer_block_list = await self.parse_answer(
                    session_id,
                    session_state.host_code_kernel_id,
                    answer,
                    code_task_manager,
                    reference_manager,
                )

                if req.mode == "online_deployment":
                    yield SendTaskStreamingResponse(
                        id=request_id,
                        result=TaskArtifactUpdateEvent(
                            id=task_id,
                            metadata={
                                "message_content": answer_message_content,
                                "block_list": answer_block_list,
                                "key": f"{key}_assistant_answer_{current_step}",
                            },
                        ),
                    )
                assistant_message = {"role": "assistant", "content": reasoning_message_content + answer_message_content}

                history_messages.extend(thought_messages)
                thought_messages.clear()
                history_messages.append(assistant_message)
                break
        resp = await self.complete_streaming_response(request_id=request_id, task_id=task_id)
        yield resp

    def save_rollout(self, state: SessionState, rollout: dict, rollout_save_dir: Optional[str] = None):
        if not rollout_save_dir:
            log_dir = os.getenv("LOG_DIR", "output/logs")
            agent_id = state.main_agent_id
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            save_dir = Path(log_dir) / "agents" / agent_id / "rollout" / date_str
            save_dir.mkdir(parents=True, exist_ok=True)
            rollout_save_dir = save_dir
        else:
            rollout_save_dir: Path = Path(rollout_save_dir)
            if not rollout_save_dir.exists():
                rollout_save_dir.mkdir(parents=True, exist_ok=True)
                logger.success(f"Rollout save directory created at {rollout_save_dir}")

        session_id = state.session_id
        messages_filepath = rollout_save_dir / f"{session_id}.jsonl"
        data = rollout["data"]
        append_to_json_list([data], messages_filepath)
        logger.success(f"Rollout saved to {messages_filepath}")

    def build_compact_messages(self, compact_prompt: str, messages: list[DialogData]):
        system_message = {"role": "system", "content": [{"type": "text", "text": "You are a helpful AI assistant tasked with summarizing conversations."}]}
        compact_messages = [msg for msg in messages if msg["role"] not in ["system", "developer"]]  # = history_messages + thought_messages
        user_message = {"role": "user", "content": [{"type": "text", "text": compact_prompt}]}
        # 如果现在正在尝试进行工具调用，则打断工具调用，转为压缩总结
        last_message = compact_messages[-1] if len(compact_messages) > 0 else None
        if last_message and last_message["role"] == "assistant" and "tool_calls" in last_message:
            interrupt_output = """The user doesn't want to proceed with this tool use. \
The tool use was rejected (eg. if it was a file edit, the new_string was NOT written to the file). \
STOP what you are doing and wait for the user to tell you how to proceed.

[Request interrupted by user for tool use]\
"""
            tool_calls = last_message["tool_calls"]
            for tool_call in tool_calls:
                call_id = tool_call["id"]
                compact_messages.append({"role": "tool", "content": [{"type": "text", "text": interrupt_output}], "tool_call_id": call_id})
        compact_messages = [system_message] + compact_messages + [user_message]
        return compact_messages

    async def wrap_user_message_content(
        self,
        message_content: list[ContentData],
        block_list: list[BlockData],
        allowed_name2tool: dict[str, BaseTool],
        is_first_turn: bool,
        is_compact: bool = False,
    ):
        """Wrap user message content with additional context: memory, todo list, system reminders.

        Args:
            message_content (list[ContentData]): The main content of the user message.
            block_list (list[BlockData]): The list of blocks associated with the message.
            allowed_name2tool (dict[str, ToolData]): The mapping of allowed tool names to their data.
            is_first_turn (bool): Whether this is the first turn of the conversation.
            is_compact (bool, optional): Whether to use a compact representation. Defaults to False.

        Returns:
            tuple: The wrapped message content and block list.
        """
        prefix_content = []
        suffix_content = []
        if is_first_turn:
            # 第一轮
            if MemoryTool.NAME in allowed_name2tool:
                memory_tool: MemoryTool = allowed_name2tool[MemoryTool.NAME]
                memory_filepath = memory_tool.memory_filepath
                memory_text = load_text(memory_filepath)
                prefix_content.append({"type": "text", "text": f"<memory>\n{memory_text}\n</memory>"})

            if TodoWriteTool.NAME in allowed_name2tool:
                todo_write_tool: TodoWriteTool = allowed_name2tool[TodoWriteTool.NAME]
                todo_result = await todo_read(todo_write_tool.todo_filepath)
                suffix_content.append({"type": "text", "text": "<system-reminder>"})
                suffix_content.extend(todo_result.message_content)
                suffix_content.append({"type": "text", "text": "</system-reminder>"})
        if len(prefix_content) > 0:
            prefix_content.append({"type": "text", "text": f"User Query:\n\n"})

        # if suffix_content:
        #     query = content_to_text(user_message_content)
        #     nlu = self.query_nlu(query)
        #     current_time = datetime.datetime.now()
        #     current_time_str = format_datetime_with_holiday(current_time, language=language)

        #     system_reminders = []
        #     system_reminders.append(f"Current time: {current_time_str}")
        #     if tool_task_manager.target_directory:
        #         system_reminders.append(f"Current directory: {tool_task_manager.target_directory}")
        #     if nlu:
        #         system_reminders.append(f"NLU: {nlu}")
        #     if system_reminders:
        #         suffix_content.append({"type": "text", "text": f"<system-reminder>\n{'\n'.join(system_reminders)}\n</system-reminder>"})
        new_message_content = prefix_content + message_content + suffix_content
        new_block_list = prefix_content + block_list + suffix_content
        return new_message_content, new_block_list

    async def parse_answer(
        self,
        session_id: str,
        kernel_id: str,
        answer: str,
        code_task_manager: CodeTaskManager,
        reference_manager: ReferenceManager,
    ):
        # 处理 apply
        message_content: list[ContentData] = []
        block_list: list[BlockData] = []
        text_blocks = parse_text_with_apply(answer)
        for text_block in text_blocks:
            if text_block["type"] == "text":
                message_content.append(text_block)
                block_list.append(text_block)
            elif text_block["type"] == "apply":
                code = text_block["text"]
                code_result = await self.execute_code(session_id, kernel_id, code, code_task_manager)
                if not code_result:
                    # apply 代码块执行失败
                    logger.warning("Code execution failed")
                    continue
                prefix_message_content = [
                    {"type": "text", "text": "<code-interpreter>"},
                    {"type": "text", "text": code},
                    {"type": "text", "text": "</code-interpreter>"},
                    {"type": "text", "text": "<code-result>"},
                ]
                suffix_message_content = [
                    {"type": "text", "text": "</code-result>"},
                ]
                tool_result = ToolResult.from_dict(code_result)
                tool_result = reference_manager.process_tool_result(tool_result)
                code_message_content = tool_result.message_content
                code_block_list = tool_result.block_list
                full_message_content = prefix_message_content + code_message_content + suffix_message_content
                full_block_list = prefix_message_content + code_block_list + suffix_message_content
                message_content.extend(full_message_content)
                block_list.extend(full_block_list)
        return message_content, block_list

    def _validate_request(self, request: Union[SendTaskRequest, SendTaskStreamingRequest]):
        task_send_params: TaskSendParams = request.params
        try:
            req = SessionRequest.model_validate(task_send_params.payload)
        except Exception as e:
            logger.error(f"Invalid request payload: {e}")
            return InvalidParamsError(message=str(e))
        return req

    async def on_get_task(self, request):
        return await super().on_get_task(request)

    async def on_cancel_task(self, request):
        return await super().on_cancel_task(request)

    async def on_get_task_push_notification(self, request):
        return await super().on_get_task_push_notification(request)

    async def on_resubscribe_to_task(self, request):
        return await super().on_resubscribe_to_task(request)

    async def on_set_task_push_notification(self, request):
        return await super().on_set_task_push_notification(request)
