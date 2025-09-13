from transformers import PreTrainedModel, PreTrainedTokenizerBase
from typing import List, Optional, Any, Dict, Tuple
from synthetic.hooks import (
    Hook,
    OnTokenHook,
    OnEOSHook,
    HookType,
    TokenEvent,
    EOSEvent,
    CommandHook,
)
from synthetic.exceptions import EOSException, StopCriteria
from synthetic.commands import Command, CommandSignature
from jinja2 import Template, StrictUndefined, Undefined
import torch
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class GenerationOutput:
    input: Dict[str, Any]
    step: int

    extra: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, input: Dict[str, Any], step: int, **kwargs) -> None:
        self.input = input
        self.step = step
        self.extra = kwargs

    def __getattr__(self, name: str) -> Any:
        if name in self.extra:
            return self.extra[name]
        raise AttributeError(f"{name} not found")


class Transformer:

    model: PreTrainedModel
    tokenizer: PreTrainedTokenizerBase
    device: str

    prompt_template: Template

    max_new_tokens: Optional[int]
    greedy: bool

    command_signature: CommandSignature

    _hooks: List[Hook]
    _commands: List[Command]

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizerBase,
        device: str = "cpu",
        eos_token: Optional[str] = None,
        prompt_template: Optional[str] = None,
        strict: bool = False,
        max_new_tokens: Optional[int] = None,
        greedy: bool = True,
        command_signature: CommandSignature = CommandSignature("<<", ":", "|", ">>"),
        hooks: List[Hook] = [],
        commands: List[Command] = [],
    ) -> None:

        self.model: PreTrainedModel = model.to(device)  # type: ignore
        self.tokenizer = tokenizer
        self.device = device

        if eos_token:
            self.eos_token = self.tokenizer.convert_tokens_to_ids(eos_token)  # type: ignore
        elif self.model.config.eos_token_id:
            self.eos_token = self.model.config.eos_token_id
        else:
            raise ValueError("No EOS token provided!")

        if prompt_template:
            undefined = StrictUndefined if strict else Undefined
            self.prompt_template = Template(prompt_template, undefined=undefined)
        else:
            self.prompt_template = Template("{{ inputs }}", undefined=StrictUndefined)

        self.max_new_tokens = max_new_tokens
        self.greedy = greedy

        self.command_signature = command_signature

        self._hooks = hooks
        self._commands = commands

    @staticmethod
    def _build_command_dict(commands: List[Command]) -> Dict[str, Command]:
        name_counts = Counter(cmd.name for cmd in commands)

        result: Dict[str, Command] = {}
        counters: Dict[str, int] = {}

        for cmd in commands:
            base_name = cmd.name
            if name_counts[base_name] == 1:
                # Unique name, no suffix
                key = base_name
            else:
                # Shared name, add suffix
                counters[base_name] = counters.get(base_name, 0) + 1
                key = f"{base_name}-{counters[base_name]}"
            result[key] = cmd

        return result

    @staticmethod
    def _sort_hooks(hooks: List[Hook]) -> Tuple[List[OnTokenHook], List[OnEOSHook]]:
        on_token_hooks = []
        on_eos_hooks = []

        for hook in hooks:
            if hook.hook_type == HookType.ON_TOKEN:
                on_token_hooks.append(hook)
            elif hook.hook_type == HookType.ON_EOS:
                on_eos_hooks.append(hook)
            else:
                raise ValueError("Failed to sort hooks as an invalid hook was found.")

        return (on_token_hooks, on_eos_hooks)

    @staticmethod
    def _run_on_token_hooks(event: TokenEvent, hooks: List[OnTokenHook]) -> TokenEvent:

        for hook in hooks:

            if not isinstance(hook, OnTokenHook):
                raise ValueError(f"Tried to run '{hook}' as an OnTokenHook.")

            event = hook(event)

        return event

    @staticmethod
    def _run_on_eos_hooks(event: EOSEvent, hooks: List[OnEOSHook]) -> EOSEvent:

        for hook in hooks:

            if not isinstance(hook, OnEOSHook):
                raise ValueError(f"Tried to run '{hook}' as an OnEOSHook.")

            event = hook(event)

        return event

    def generate(self, **kwargs: Any) -> GenerationOutput:

        command_dict = self._build_command_dict(self._commands)

        on_token_hooks, on_eos_hooks = self._sort_hooks(
            [
                CommandHook(
                    command_signature=self.command_signature,
                    tokenizer=self.tokenizer,
                    device=self.device,
                    commands=command_dict,
                )
            ]
            + self._hooks
        )

        print(on_token_hooks)
        print(on_eos_hooks)

        prompt = self.prompt_template.render(**kwargs)

        input_ids = (
            torch.tensor(self.tokenizer.encode(prompt), dtype=torch.int)
            .unsqueeze(0)
            .to(self.device)
        )
        past_key_values = None

        step = 0

        try:
            while self.max_new_tokens is None or step < self.max_new_tokens:

                step += 1

                outputs = self.model(
                    input_ids=input_ids,
                    past_key_values=past_key_values,
                    use_cache=True,
                )

                logits = outputs.logits[:, -1, :]
                past_key_values = outputs.past_key_values

                if self.greedy:
                    next_token = torch.argmax(logits, dim=-1)
                else:
                    probs = torch.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1).squeeze(-1)

                if next_token == self.eos_token:
                    raise EOSException(stop_criteria=StopCriteria.EOS_TOKEN)

                input_ids = torch.cat([input_ids, next_token.unsqueeze(-1)], dim=-1)

                token_event = TokenEvent(
                    input_ids=input_ids, past_key_values=past_key_values, step=step
                )
                token_event = self._run_on_token_hooks(token_event, on_token_hooks)

                input_ids = token_event.input_ids
                past_key_values = token_event.past_key_values

            raise EOSException(stop_criteria=StopCriteria.TOKEN_LIMIT)

        except EOSException as e:

            eos_event = EOSEvent(
                step=step,
                eos_exception=e,
                input_ids=input_ids,
                past_key_values=past_key_values,  # type: ignore
                output={"output": self.tokenizer.batch_decode(input_ids)[0]},
            )

            eos_event = self._run_on_eos_hooks(eos_event, on_eos_hooks)

        return GenerationOutput(input=kwargs, step=step, **eos_event.output)
