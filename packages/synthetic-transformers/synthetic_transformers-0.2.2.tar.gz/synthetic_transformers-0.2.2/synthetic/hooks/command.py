from synthetic.hooks import TokenEvent, OnTokenHook
from synthetic.commands import (
    CommandSignature,
    Command,
    CommandInput,
    CommandOutput,
    CommandExecution,
)
from transformers import PreTrainedTokenizerBase
from typing import Dict
import torch


class CommandHook(OnTokenHook):

    command_signature: CommandSignature
    tokenizer: PreTrainedTokenizerBase
    commands: Dict[str, Command]
    device: str

    def __init__(
        self,
        command_signature: CommandSignature,
        tokenizer: PreTrainedTokenizerBase,
        commands: Dict[str, Command],
        device: str,
    ) -> None:
        super().__init__()
        self.command_signature = command_signature
        self.tokenizer = tokenizer
        self.commands = commands
        self.device = device

    def __call__(self, event: TokenEvent) -> TokenEvent:
        text = self.tokenizer.batch_decode(event.input_ids)[0]
        match = self.command_signature.match(text)

        if match:

            command = self.commands.get(match.command_name)

            if command is None:
                output = CommandOutput(
                    error="Invalid command name.", input_ids=event.input_ids
                )
            else:
                command_input = CommandInput(
                    input=match.input,
                    input_ids=event.input_ids,
                )

                output = command.execute(command_input)

                event.command_executions.append(
                    CommandExecution(
                        step=event.step,
                        command_name=match.command_name,
                        command_input=command_input,
                        command_output=output,
                    )
                )

            text = self.tokenizer.batch_decode(output.input_ids)[0]
            if output.error:
                text = self.command_signature.replace_partial_at_end(
                    text, f"Error: {output.error}"
                )
            elif output.output:
                text = self.command_signature.replace_partial_at_end(
                    text, output.output
                )
            else:
                raise ValueError(
                    "CommandOutput should contain at least one of 'error' or 'data' properties."
                )

            input_ids = (
                torch.tensor(self.tokenizer.encode(text), dtype=torch.int)
                .unsqueeze(0)
                .to(self.device)
            )

            event.input_ids = input_ids

        return event
