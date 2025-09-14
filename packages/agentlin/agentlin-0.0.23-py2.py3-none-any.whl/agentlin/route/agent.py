from typing import Any, Literal, Optional, Type
import uuid

from pydantic import BaseModel

from agentlin.core.types import ContentData, DialogData, ToolData
from agentlin.route.agent_config import AgentConfig
from agentlin.route.session_manager import SessionRequest, SessionTaskManager


class Agent(SessionTaskManager):
    pass