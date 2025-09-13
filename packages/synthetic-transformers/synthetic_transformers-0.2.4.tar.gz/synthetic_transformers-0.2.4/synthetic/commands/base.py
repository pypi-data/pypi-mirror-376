from dataclasses import dataclass
from typing import Callable, Optional
import torch


@dataclass
class CommandInput:
    input: str
    input_ids: torch.Tensor


class CommandOutput:
    input_ids: torch.Tensor
    output: Optional[str]
    error: Optional[str]

    def __init__(
        self,
        input_ids: torch.Tensor,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        if output is None and error is None:
            raise ValueError(
                "At least one of the 'output' or 'error' arguments has to be not None."
            )

        self.input_ids = input_ids
        self.output = output
        self.error = error


@dataclass
class CommandExecution:
    step: int
    command_name: str
    command_input: CommandInput
    command_output: CommandOutput


class Command:
    name: str
    execute: Callable[[CommandInput], CommandOutput]

    def __init__(
        self, name: str, execute: Callable[[CommandInput], CommandOutput]
    ) -> None:
        self.name = name
        self.execute = execute
