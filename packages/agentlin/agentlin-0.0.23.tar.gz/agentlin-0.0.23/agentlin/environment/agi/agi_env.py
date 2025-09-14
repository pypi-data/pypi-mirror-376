"""AGI 工具环境

基于 `tool_env.AsyncToolEnvironment` 实现，将原先 `env.py` 中以类 `ArcAgi3` + 手工调度工具的逻辑
规范化为：

1. 使用统一的 ToolEnvironment/AsyncToolEnvironment 抽象
2. 通过 `aforward(state, tool_name=..., tool_arguments=...)` 进行状态转移
3. 环境状态对象携带：
   - 当前底层 `EnvState`（游戏 id, card id, guid, experiences）
   - 最近一次工具调用返回的内容（文本 / frame 等）
4. 支持 RESET 动作重新创建底层游戏状态

与 `QAListEnv` / `QAListState` 的对应关系：
* QAListEnv.forward -> 这里的 `aforward`
* QAListState(TextState) -> 这里自定义 `AGIEnvState(ToolEnvState)` 承载特有字段

与旧 `ArcAgi3` 的对应映射：
* create_state -> `_create_underlying_state`
* step -> 通过工具调用 `TakeAction` 触发（tool_name='TakeAction', tool_arguments={'action': ..., 'reason': {...}}）
* list_tools -> 继承自基类 (`list_tools`) （包装后的工具数据）

使用示例：
```python
from agentlin.environment.agi.agi_env import AGIToolEnvironment
from agentlin.environment.agi.client import GameAction

env = AGIToolEnvironment(debug=True)
state = env.provide_initial_state()

# 第一次行动
import asyncio
state = asyncio.run(env.aforward(state,
    tool_name='TakeAction',
    tool_arguments={'action': GameAction.ACTION1, 'reason': {'thought': 'try up'}}
))

# RESET
state = asyncio.run(env.aforward(state,
    tool_name='TakeAction',
    tool_arguments={'action': GameAction.RESET}
))
```
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, List

from loguru import logger

from agentlin.core.types import BaseTool, ToolResult
from agentlin.environment.tool_env import AsyncToolEnvironment, ToolEnvState
from agentlin.environment.agi.client import (
    ARC_AGI_Client,
    FrameData,
    GameAction,
    generate_grid_text,
    generate_llm_friendly_text,
)
from agentlin.environment.agi.env import EnvState, Experience, EnvTool  # 复用已有结构 & 工具


class AGIEnvState(ToolEnvState):
    """封装底层 EnvState 的环境状态。

    content: 继承自 ToolEnvState，保存文本/可视化内容
    env_state: 底层游戏状态（包含 game_id, card_id, guid, experiences）
    last_frame: 最近一次动作后的 FrameData（便于外部渲染）
    """

    def __init__(
        self,
        env_state: EnvState,
        content: List[Dict[str, Any]],
        tools_available: Optional[List[str]] = None,
        session_data: Optional[Dict[str, Any]] = None,
        last_frame: Optional[FrameData] = None,
        done: bool = False,
    ):
        super().__init__(
            content=content,
            tools_available=tools_available,
            session_data=session_data,
            done=done,
        )
        self.env_state = env_state
        self.last_frame = last_frame

    def _repr_mimebundle_(self):  # 富展示
        bundle = super()._repr_mimebundle_()
        bundle.setdefault("application/agentlin.agi.env.v1+json", {})
        bundle["application/agentlin.agi.env.v1+json"].update(
            {
                "game_id": self.env_state.game_id,
                "card_id": self.env_state.card_id,
                "guid": self.env_state.guid,
                "experiences": [e.model_dump() for e in self.env_state.experiences],
                "done": self.done,
            }
        )
        return bundle


class AGIToolEnvironment(AsyncToolEnvironment):
    """ARC-AGI-3 工具环境实现 (异步)。"""

    def __init__(self, debug: bool = False, info: Optional[Dict[str, str]] = None):
        self.debug = debug
        # 初始化客户端配置
        api_key = os.getenv("ARC_API_KEY")
        scheme = os.getenv("SCHEME", "http")
        host = os.getenv("HOST", "localhost")
        port = os.getenv("PORT", "8001")
        if (scheme == "http" and str(port) == "80") or (scheme == "https" and str(port) == "443"):
            root_url = f"{scheme}://{host}"
        else:
            root_url = f"{scheme}://{host}:{port}"
        logger.info(f"连接 ARC-AGI-3 API: {root_url}")
        self.client = ARC_AGI_Client(root_url, api_key)
        # 保存当前唯一状态（一个 scorecard 视为一个环境实例）。如需多实例，可扩展为 id->state
        self._env_state: Optional[EnvState] = None
        super().__init__(info=info)

    # ------------------------------------------------------------------
    # 工具注册
    # ------------------------------------------------------------------
    def _register_tools(self):  # sync（构造期调用）
        take_action_tool = EnvTool(client=self.client)
        self.add_tool(take_action_tool)

    # ------------------------------------------------------------------
    # 底层状态创建 / 重置
    # ------------------------------------------------------------------
    def _create_underlying_state(self, tags: Optional[List[str]] = None) -> EnvState:
        if tags is None:
            tags = ["demo", "example"]
        logger.info("创建新的计分卡 (scorecard) ...")
        card_id = self.client.open_scorecard(tags=tags)
        logger.info(f"计分卡已创建: {card_id}")
        games = self.client.get_games()
        if not games:
            raise RuntimeError("No available games returned by ARC_AGI_Client.get_games()")
        # 使用第一个游戏或固定 ID（保持与旧实现一致）
        game_id = games[0]
        # 若想强制演示某个指定 game，可在外部通过环境变量传入
        fixed_game_id = os.getenv("ARC_FIXED_GAME_ID")
        if fixed_game_id:
            game_id = fixed_game_id
        logger.info(f"使用游戏: {game_id}")
        state = EnvState(game_id=game_id, card_id=card_id)
        self._env_state = state
        return state

    # ------------------------------------------------------------------
    # 初始状态
    # ------------------------------------------------------------------
    def provide_initial_state(self) -> AGIEnvState:  # 覆写基类
        if self._env_state is None:
            env_state = self._create_underlying_state()
        else:
            env_state = self._env_state
        help_text = (
            "AGI 工具环境已初始化. 使用 aforward(state, tool_name='TakeAction', tool_arguments={'action': GameAction.ACTION1}) 进行动作。\n"
            "可用工具: " + ", ".join(self.get_available_tool_names())
        )
        return AGIEnvState(
            env_state=env_state,
            content=[{"type": "text", "text": help_text}],
            tools_available=self.get_available_tool_names(),
            session_data={"created": True},
            last_frame=None,
            done=False,
        )

    # ------------------------------------------------------------------
    # 异步工具调用处理
    # ------------------------------------------------------------------
    async def _ahandle_tool_call(self, state: AGIEnvState, tool_name: str, tool_arguments: Dict[str, Any]):
        # 若请求 RESET，则重置底层状态再返回提示，不真正调用底层 TakeAction
        reset_flag = False
        action_obj = tool_arguments.get("action")
        if action_obj == GameAction.RESET:
            reset_flag = True
            env_state = self._create_underlying_state()
            msg = "环境已重置 (RESET). 请继续选择动作。"
            return AGIEnvState(
                env_state=env_state,
                content=[{"type": "text", "text": msg}],
                tools_available=self.get_available_tool_names(),
                session_data={**state.session_data, "reset": True},
                last_frame=None,
                done=False,
            )

        # 确保底层状态存在
        if self._env_state is None:
            self._create_underlying_state()
        env_state = self._env_state

        # 将底层 env_state 注入工具调用参数
        tool_arguments = dict(tool_arguments)  # 浅拷贝防副作用
        tool_arguments.setdefault("state", env_state)

        # 执行工具（TakeAction）
        result: ToolResult = await self.execute_tool(tool_name, tool_arguments)

        # 若执行失败（error block），保持原状态，仅添加错误提示
        has_error = any(b.get("type") == "error" for b in result.block_list or [])
        if has_error:
            return AGIEnvState(
                env_state=env_state,
                content=state.content + (result.message_content or []),
                tools_available=self.get_available_tool_names(),
                session_data=state.session_data,
                last_frame=getattr(state, "last_frame", None),
                done=False,
            )

        # 从 block_list 中解析 frame 数据（若存在）
        last_frame: Optional[FrameData] = None
        if result.block_list:
            for block in result.block_list:
                if block.get("type") == "frame":
                    data = block.get("data")
                    try:
                        last_frame = FrameData(**data)
                    except Exception:  # 容错
                        logger.warning("Failed to parse FrameData from tool result block")

        # 生成下一状态展示文本（追加）
        extra_content = result.message_content or []
        if last_frame is not None and last_frame.frame:
            grid_text = generate_grid_text(last_frame.frame, use_colors=False)
            extra_content.append({"type": "text", "text": f"Frame:\n{grid_text}"})

        return AGIEnvState(
            env_state=env_state,
            content=state.content + extra_content,
            tools_available=self.get_available_tool_names(),
            session_data=state.session_data,
            last_frame=last_frame or getattr(state, "last_frame", None),
            done=False,
        )

    # ------------------------------------------------------------------
    # 便捷方法（可选）
    # ------------------------------------------------------------------
    async def take_action(self, state: AGIEnvState, action: GameAction, reason: Optional[Dict[str, Any]] = None) -> AGIEnvState:
        """便捷封装，等价于 aforward(... 'TakeAction', {'action': action, 'reason': reason})"""
        return await self.aforward(
            state,
            tool_name="TakeAction",
            action=action,
            reason=reason or {},
        )

    # 明确声明：同步 forward 不可用
    def _handle_tool_call(self, *args, **kwargs):  # type: ignore[override]
        raise NotImplementedError("Use aforward() (异步) 进行状态转移")


__all__ = [
    "AGIToolEnvironment",
    "AGIEnvState",
]
import os
from typing import Optional, Dict, Any, List
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from agentlin.environment.tool_env import AsyncToolEnvironment, ToolEnvState
from agentlin.environment.agi.client import ARC_AGI_Client, FrameData, GameAction, generate_grid_text, generate_llm_friendly_text
from agentlin.core.types import BaseTool, ToolResult, ContentData


class AGIExperience(BaseModel):
    """AGI 环境中的经验记录"""
    reason: Dict[str, Any] = {}
    action: GameAction
    frame: FrameData


class AGIEnvState(ToolEnvState):
    """AGI 环境状态，扩展了基础的工具环境状态"""
    def __init__(
        self,
        content: List[ContentData],
        game_id: str,
        card_id: str,
        guid: Optional[str] = None,
        experiences: List[AGIExperience] = None,
        tools_available: List[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
        done: bool = False,
    ):
        super().__init__(content, tools_available, session_data, done)
        self.game_id = game_id
        self.card_id = card_id
        self.guid = guid
        self.experiences = experiences or []

    def check_validity(self) -> bool:
        rules = [
            super().check_validity(),
            isinstance(self.game_id, str) and len(self.game_id) > 0,
            isinstance(self.card_id, str) and len(self.card_id) > 0,
            isinstance(self.experiences, list),
        ]
        return all(rules)

    def _get_display_text(self) -> str:
        """获取显示文本"""
        text_parts = []
        text_parts.append(f"Game ID: {self.game_id}")
        text_parts.append(f"Card ID: {self.card_id}")
        text_parts.append(f"Experiences: {len(self.experiences)}")

        if self.content:
            text_content = [item.get("text", "") for item in self.content if item.get("type") == "text"]
            if text_content:
                text_parts.append("Current State:")
                text_parts.extend(text_content)

        return "\n".join(text_parts)

    def _repr_mimebundle_(self):
        bundle = super()._repr_mimebundle_()
        bundle.update({
            "application/agentlin.agi.env.v1+json": {
                "game_id": self.game_id,
                "card_id": self.card_id,
                "guid": self.guid,
                "experiences_count": len(self.experiences),
                "current_frame": self.experiences[-1].frame.model_dump() if self.experiences else None,
            }
        })
        return bundle


class AGIActionTool(BaseTool):
    """AGI 环境中的动作执行工具"""
    def __init__(self, client: ARC_AGI_Client):
        schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["RESET", "ACTION1", "ACTION2", "ACTION3", "ACTION4"],
                    "description": "The action to take. ACTION1 (Move Up), ACTION2 (Move Down), ACTION3 (Move Left), ACTION4 (Move Right), RESET (Reset Game)"
                },
                "reason": {
                    "type": "string",
                    "description": "Detailed reasoning for choosing this action",
                    "maxLength": 2000
                },
                "short_description": {
                    "type": "string",
                    "description": "Brief description of the action",
                    "maxLength": 500
                },
                "hypothesis": {
                    "type": "string",
                    "description": "Current hypothesis about game mechanics",
                    "maxLength": 2000
                },
                "aggregated_findings": {
                    "type": "string",
                    "description": "Summary of discoveries and learnings so far",
                    "maxLength": 2000
                },
                "util_code": {
                    "type": "string",
                    "description": "Code snippets or examples that may help in understanding or solving the problem",
                    "maxLength": 10000
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }

        super().__init__(
            name="take_action",
            title="Take Action in AGI Environment",
            description="Take an action in the ARC-AGI-3 environment. Available actions are RESET, ACTION1, ACTION2, ACTION3, ACTION4.",
            parameters=schema,
        )
        self.client = client

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        action_name = params.get("action")
        reason = {
            "reason": params.get("reason", ""),
            "short_description": params.get("short_description", ""),
            "hypothesis": params.get("hypothesis", ""),
            "aggregated_findings": params.get("aggregated_findings", ""),
            "util_code": params.get("util_code", ""),
        }

        # 从params中获取状态信息（这些会在环境中设置）
        game_id = params.get("game_id")
        card_id = params.get("card_id")
        guid = params.get("guid")

        if not game_id or not card_id:
            return ToolResult(
                message_content=[{"type": "text", "text": "Error: game_id and card_id are required"}],
                block_list=[{"type": "error", "message": "Missing game_id or card_id"}]
            )

        # 转换动作名称为GameAction枚举
        try:
            action = GameAction[action_name]
        except KeyError:
            return ToolResult(
                message_content=[{"type": "text", "text": f"Error: Invalid action '{action_name}'"}],
                block_list=[{"type": "error", "message": f"Invalid action: {action_name}"}]
            )

        try:
            # 执行动作
            frame = self.client.execute_action(action=action, game_id=game_id, card_id=card_id, guid=guid)

            # 获取网格数据
            grid = frame.frame[-1] if frame.frame else []
            frame.frame = grid

            # 生成显示内容
            content = self._generate_screen_content(grid)

            return ToolResult(
                message_content=content,
                block_list=[{
                    "type": "agi_frame",
                    "data": {
                        "frame": frame.model_dump(),
                        "action": action_name,
                        "reason": reason,
                        "guid": frame.guid,
                    }
                }]
            )
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return ToolResult(
                message_content=[{"type": "text", "text": f"Error executing action: {str(e)}"}],
                block_list=[{"type": "error", "message": str(e)}]
            )

    def _generate_screen_content(self, grid: List[List[int]]) -> List[ContentData]:
        """生成屏幕内容"""
        text = generate_llm_friendly_text(grid)
        return [{"type": "text", "text": text}]


class AGIEnvironment(AsyncToolEnvironment):
    """AGI 环境实现"""

    def __init__(self, debug: bool = False):
        self.debug = debug

        # 从环境变量获取配置
        api_key = os.getenv("ARC_API_KEY")
        scheme = os.getenv("SCHEME", "http")
        host = os.getenv("HOST", "localhost")
        port = os.getenv("PORT", "8001")

        if (scheme == "http" and str(port) == "80") or (scheme == "https" and str(port) == "443"):
            root_url = f"{scheme}://{host}"
        else:
            root_url = f"{scheme}://{host}:{port}"

        logger.info(f"连接到ARC-AGI-3 API: {root_url}")

        self.client = ARC_AGI_Client(root_url, api_key)
        self.active_states: Dict[str, AGIEnvState] = {}

        # 自定义信息
        info = {
            "game_started": "AGI game started successfully!",
            "game_reset": "Game has been reset.",
            "action_executed": "Action executed successfully.",
            "game_over": "Game over!",
            "help": """Available actions:
- take_action: Execute an action in the game (RESET, ACTION1, ACTION2, ACTION3, ACTION4)

<example-code>
state = env.provide_initial_state()
next_state = await env.aforward(state, tool_name='take_action', tool_arguments={
    'action': 'ACTION1',
    'reason': 'Moving up to explore the grid',
    'short_description': 'Move up'
})
</example-code>""",
        }

        super().__init__(info)

    def _register_tools(self):
        """注册AGI环境所需的工具"""
        action_tool = AGIActionTool(self.client)
        self.add_tool(action_tool)

    def create_game_session(self, tags: List[str] = None) -> AGIEnvState:
        """创建新的游戏会话"""
        if tags is None:
            tags = ["demo", "example"]

        logger.info("打开新的计分卡...")
        card_id = self.client.open_scorecard(tags=tags)
        logger.info(f"计分卡已创建: {card_id}")

        logger.info("获取可用游戏列表...")
        games = self.client.get_games()
        logger.info(f"找到 {len(games)} 个可用游戏: {games[:5]}...")

        # 选择第一个游戏
        game_id = games[0] if games else "ls20-f340c8e5138e"
        logger.info(f"使用游戏: {game_id}")

        # 创建初始状态
        state = AGIEnvState(
            content=[{"type": "text", "text": f"Game initialized: {game_id}\nCard ID: {card_id}\n\n{self.info['help']}"}],
            game_id=game_id,
            card_id=card_id,
            tools_available=self.get_available_tool_names(),
            session_data={"tags": tags}
        )

        self.active_states[card_id] = state
        return state

    async def _ahandle_tool_call(self, state: AGIEnvState, tool_name: str, tool_arguments: Dict[str, Any]) -> AGIEnvState:
        """处理工具调用"""
        if tool_name == "take_action":
            return await self._handle_action_call(state, tool_arguments)
        else:
            return self._create_error_state(f"Unknown tool: {tool_name}")

    async def _handle_action_call(self, state: AGIEnvState, tool_arguments: Dict[str, Any]) -> AGIEnvState:
        """处理动作调用"""
        # 将状态信息添加到工具参数中
        tool_arguments.update({
            "game_id": state.game_id,
            "card_id": state.card_id,
            "guid": state.guid,
        })

        # 执行工具
        result = await self.execute_tool("take_action", tool_arguments)

        # 处理结果
        if result.block_list and len(result.block_list) > 0:
            block_data = result.block_list[0]
            if block_data.get("type") == "agi_frame":
                frame_data = block_data.get("data", {})
                frame_info = frame_data.get("frame", {})
                action_name = frame_data.get("action", "")
                reason = frame_data.get("reason", {})
                new_guid = frame_data.get("guid")

                # 创建经验记录
                try:
                    action = GameAction[action_name]
                    frame = FrameData.model_validate(frame_info)
                    experience = AGIExperience(reason=reason, action=action, frame=frame)

                    # 创建新状态
                    new_state = AGIEnvState(
                        content=result.message_content,
                        game_id=state.game_id,
                        card_id=state.card_id,
                        guid=new_guid or state.guid,
                        experiences=state.experiences + [experience],
                        tools_available=state.tools_available,
                        session_data=state.session_data,
                        done=False  # 可以根据游戏状态决定是否完成
                    )

                    # 更新活跃状态
                    self.active_states[state.card_id] = new_state
                    return new_state

                except Exception as e:
                    logger.error(f"Error processing action result: {e}")
                    return self._create_error_state(f"Error processing action result: {str(e)}")

        # 如果没有有效的块数据，返回错误状态
        return self._create_error_state("Invalid action result")

    def provide_initial_state(self) -> AGIEnvState:
        """提供初始状态"""
        return self.create_game_session()

    def close_session(self, card_id: str) -> bool:
        """关闭游戏会话"""
        if card_id in self.active_states:
            try:
                result = self.client.close_scorecard(card_id=card_id)
                if result:
                    del self.active_states[card_id]
                    logger.info(f"Session closed: {card_id}")
                    return True
                else:
                    logger.warning(f"Failed to close session: {card_id}")
                    return False
            except Exception as e:
                logger.error(f"Error closing session {card_id}: {e}")
                return False
        else:
            logger.warning(f"Session not found: {card_id}")
            return False

    def render_frame(self, frame: FrameData, use_colors: bool = False):
        """渲染帧"""
        if self.debug:
            logger.debug("Rendering frame:")
        screen_as_text = generate_grid_text(frame.frame, use_colors=use_colors)
        print(screen_as_text)

    def get_session_state(self, card_id: str) -> Optional[AGIEnvState]:
        """获取会话状态"""
        return self.active_states.get(card_id)

    def list_active_sessions(self) -> List[str]:
        """列出活跃的会话"""
        return list(self.active_states.keys())
