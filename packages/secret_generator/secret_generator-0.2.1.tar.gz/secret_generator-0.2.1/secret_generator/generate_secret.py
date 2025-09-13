from dataclasses import dataclass
from random import choices, shuffle
from string import punctuation, ascii_lowercase, ascii_uppercase, digits

from .cli_helper import input_choices, input_single
from .config import CLIConfig


@dataclass(frozen=True)
class Config:
    lowercase_count: int = 3
    uppercase_count: int = 3
    punctuation_count: int = 3
    digits_count: int = 3

    url_safe_punctuation: str = "-_.~"

    default_length: int = 40
    required_part_length: int = lowercase_count + uppercase_count + punctuation_count + digits_count
    max_length: int = 4096


def generate_secret(length: int, punctuation_symbols_sequence: str = punctuation) -> str:
    symbols = f"{punctuation_symbols_sequence}{ascii_lowercase}{ascii_uppercase}{digits}"

    if punctuation_symbols_sequence == "":
        punctuation_symbols = []
    else:
        punctuation_symbols = choices(punctuation_symbols_sequence, k=Config.punctuation_count)

    lowercase_symbols = choices(ascii_lowercase, k=Config.lowercase_count)
    uppercase_symbols = choices(ascii_uppercase, k=Config.uppercase_count)
    digits_symbols = choices(digits, k=Config.digits_count)

    required_part = (
        f"{"".join(lowercase_symbols + uppercase_symbols + punctuation_symbols + digits_symbols)}"
    )

    if length < len(required_part):
        raise ValueError("Password length is too short")

    base_pass_len = length - len(required_part)
    base_part = "".join(choices(symbols, k=base_pass_len))

    total = f"{required_part}{base_part}"
    total_list = list(total)

    shuffle(total_list)
    return "".join(total_list)


def punctuation_menu() -> str | None:
    cli_args = {1: Config.url_safe_punctuation, 2: punctuation, 3: ""}
    options = {
        1: "URL safe punctuation",
        2: "All punctuation symbols",
        3: "No punctuation symbols",
    }
    return input_choices(cli_args, options, input_type=int, default_choice=2)


def password_menu() -> int:
    return input_single(
        f"Length of password ({Config.required_part_length} - {Config.max_length}):",
        input_type=int,
        comparison_operations=[
            ("ge", Config.required_part_length),
            ("le", Config.max_length),
        ],
        default_value=Config.default_length,
    )


def menu() -> None:
    punctuation_symbols = punctuation_menu()
    password_length = password_menu()

    password = generate_secret(password_length, punctuation_symbols)

    top = f"{' Secret ':{CLIConfig.line_symbols}^{CLIConfig.line_length}}"
    bottom = CLIConfig.line_symbols * CLIConfig.line_length

    print(top, password, bottom, sep="\n")


def run() -> None:
    try:
        menu()
    except KeyboardInterrupt:
        print("Cancelled")


if __name__ == "__main__":
    run()
