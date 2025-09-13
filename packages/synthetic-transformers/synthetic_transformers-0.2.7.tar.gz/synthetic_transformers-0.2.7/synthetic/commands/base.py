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


class CommandExecution:
    step: int
    command_name: str
    command_input: CommandInput
    command_output: CommandOutput

    def __init__(
        self,
        step: int,
        command_name: str,
        command_input: CommandInput,
        command_output: CommandOutput,
    ) -> None:
        self.step = step
        self.command_name = command_name
        self.command_input = CommandInput(
            input=command_input.input,
            input_ids=command_input.input_ids.detach().clone().cpu(),
        )
        self.command_output = CommandOutput(
            input_ids=command_output.input_ids.detach().clone().cpu(),
            output=command_output.output,
            error=command_output.error,
        )


class Command:
    name: str
    execute: Callable[[CommandInput], CommandOutput]

    def __init__(
        self, name: str, execute: Callable[[CommandInput], CommandOutput]
    ) -> None:
        self.name = name
        self.execute = execute
