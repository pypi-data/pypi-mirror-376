
from typing import Union

import numpy as np
from PIL.Image import Image
import torch
import torch.nn as nn

from agentlin.code_interpreter.types import ToolResponse
from agentlin.core.multimodal import image_content
from agentlin.environment.interface import IState


class ImageState(IState):
    def __init__(self, image: Union[str, np.ndarray, Image, torch.Tensor]):
        self.image = image

    def __str__(self):
        return "[image]"

    def display(self) -> ToolResponse:
        if not self.check_validity():
            message = "Invalid state"
            content = [{"type": "text", "text": message}]
        else:
            content = image_content(self.image)
        return {
            "message_content": content,
            "block_list": content,
            "data": {"done": False},
        }
