from getpass import getpass
from typing import Iterable

from .config import CLIConfig
from .operators_helper import ComparisonOperatorsType, COMPARISON_OPERATORS_INFO, compare


def print_divider(
    line_symbols: str = CLIConfig.line_symbols,
    line_length: int = CLIConfig.line_length,
) -> None:
    print(line_symbols * line_length)


def print_options(options: dict[str, str]) -> None:
    for key, value in options.items():
        print(f"{key}) {value}")


def do_comparison_operations[I](
    value: I,
    comparison_operations: Iterable[tuple[ComparisonOperatorsType, I]] = (),
) -> bool:
    results = [True]

    for operator, comparison_value in comparison_operations:
        result = compare(operator, value, comparison_value)

        if not result:
            desc = COMPARISON_OPERATORS_INFO[operator]["description"]

            print(f"Value must be {desc.lower()} {comparison_value!r}")

        results.append(result)

    return all(results)


def input_password() -> str:
    password = getpass("Input password: ")
    confirm = getpass("Confirm password: ")

    if password != confirm:
        print("❌ Passwords do not match.")
        exit(1)

    return password


def input_single[I](
    prompt: str,
    *,
    input_type: type[I],
    comparison_operations: Iterable[tuple[ComparisonOperatorsType, I]] = (),
    default_value: I | None = None,
) -> I:
    input_prompt = f"(default: {default_value!r}) > " if default_value is not None else "> "

    while True:
        print(prompt)

        try:
            value = input(input_prompt).strip()

            if value == "" and default_value is not None:
                value = default_value
                break

            value = input_type(value)
            check_compare = do_comparison_operations(value, comparison_operations)

            if check_compare:
                break

        except ValueError:
            print("--- Invalid input ---")

    print_divider()
    return value


def input_choices[I, R](
    cli_args: dict[I, R],
    options: dict[I, str],
    *,
    input_type: type[I],
    default_choice: I | None = None,
) -> R:
    print_options(options)
    input_prompt = f"(default: {default_choice!r}) > " if default_choice is not None else "> "

    while True:
        try:
            choice = input(input_prompt).strip()

            if choice == "" and default_choice is not None and default_choice in cli_args:
                choice = default_choice
                break

            choice = input_type(choice)

            if choice in cli_args:
                break

        except ValueError:
            print("--- Invalid choice ---")

        print("Please choose one of the following options:")
        print_options(options)

    print_divider()
    return cli_args[choice]
