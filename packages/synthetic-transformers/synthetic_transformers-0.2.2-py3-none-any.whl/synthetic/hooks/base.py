from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import torch
from synthetic.exceptions import EOSException
from synthetic.commands import CommandExecution
from typing import Dict, Any, List


class HookType(Enum):
    ON_TOKEN = "on_token"
    ON_EOS = "on_eos"


@dataclass
class Event:
    step: int
    input_ids: torch.Tensor
    past_key_values: torch.Tensor
    command_executions: List[CommandExecution] = field(default_factory=list)


class Hook(ABC):
    hook_type: HookType

    def __init__(self) -> None:
        pass

    @abstractmethod
    def __call__(self, event) -> Event:
        pass


## --- ON_TOKEN --------


@dataclass
class TokenEvent(Event):
    pass


class OnTokenHook(Hook):
    hook_type = HookType.ON_TOKEN

    @abstractmethod
    def __call__(self, event: TokenEvent) -> TokenEvent:
        pass


## --- ON_EOS ---------


@dataclass(kw_only=True)
class EOSEvent(Event):
    eos_exception: EOSException
    output: Dict[str, Any]


class OnEOSHook(Hook):
    hook_type = HookType.ON_EOS

    @abstractmethod
    def __call__(self, event: EOSEvent) -> EOSEvent:
        pass
