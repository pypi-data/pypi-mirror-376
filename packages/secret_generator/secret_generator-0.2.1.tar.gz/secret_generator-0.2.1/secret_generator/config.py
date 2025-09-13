from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    encoding: str = "UTF-8"


@dataclass(frozen=True)
class CLIConfig:
    line_symbols: str = "-"
    line_length: int = 70
