from dataclasses import dataclass
from typing import Optional


@dataclass
class SignatureMatch:
    command_name: str
    input: str


class CommandSignature:
    start_string: str
    name_input_separation: str
    input_output_separation: str
    end_string: str

    def __init__(
        self,
        start_string: str,
        name_input_separation: str,
        input_output_separation: str,
        end_string: str,
    ) -> None:
        if not start_string:
            raise ValueError("The start_string should not be empty.")
        if not name_input_separation:
            raise ValueError("The name_input_separation should not be empty.")
        if not input_output_separation:
            raise ValueError("The input_output_separation should not be empty.")
        if not end_string:
            raise ValueError("The end_string should not be empty.")

    def match(self, text: str) -> Optional[SignatureMatch]:
        if not text.endswith(self.input_output_separation):
            return None

        # Extract the portion between start_string and the last input_output_separation
        before_sep = text[: -len(self.input_output_separation)]

        # Find the last start_string
        start_idx = before_sep.rfind(self.start_string)
        if start_idx == -1:
            return None

        inner = before_sep[start_idx + len(self.start_string) :]

        # Must contain name_input_separation
        if self.name_input_separation not in inner:
            return None

        name, input_str = inner.split(self.name_input_separation, 1)

        return SignatureMatch(command_name=name.strip(), input=input_str.strip())

    def dump_to_string(self, command_name: str, input: str, output: str) -> str:
        return (
            f"{self.start_string}"
            f"{command_name}{self.name_input_separation}{input}"
            f"{self.input_output_separation}{output}"
            f"{self.end_string}"
        )

    def replace_partial_at_end(self, text: str, output: str) -> str:
        m = self.match(text)
        if not m:
            return text

        # Find where the partial signature starts
        start_idx = text.rfind(self.start_string)
        # Replace it with the full signature
        return text[:start_idx] + self.dump_to_string(m.command_name, m.input, output)
