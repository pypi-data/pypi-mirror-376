from operator import lt, le, eq, ne, ge, gt
from typing import Literal

COMPARISON_OPERATORS_INFO = {
    "lt": {"operator": lt, "description": "Less than"},
    "le": {"operator": le, "description": "Less or equal"},
    "eq": {"operator": eq, "description": "Equal"},
    "ne": {"operator": ne, "description": "Not equal"},
    "ge": {"operator": ge, "description": "Greater or equal"},
    "gt": {"operator": gt, "description": "Greater than"},
}

type ComparisonOperatorsType = Literal["lt", "le", "eq", "ne", "ge", "gt"]


def compare[A, B](operator_type: ComparisonOperatorsType, a: A | B, b: A | B) -> bool:
    return COMPARISON_OPERATORS_INFO[operator_type]["operator"](a, b)
