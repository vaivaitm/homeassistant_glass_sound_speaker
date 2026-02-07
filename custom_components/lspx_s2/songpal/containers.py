"""Minimal container types used by the LSPX-S2 integration.

These mirror the small subset of types the integration expects from
`songpal.containers`.
"""

from typing import Any, Iterable, List, Optional


class Option:
    def __init__(self, value: Any, title: Optional[str] = None, isAvailable: bool = True) -> None:
        self.value = value
        self.title = title or str(value)
        self.isAvailable = isAvailable


class Setting:
    def __init__(self, target: Optional[str] = None, currentValue: Optional[Any] = None, candidate: Optional[Iterable[Option]] = None) -> None:
        self.target = target
        self.currentValue = currentValue
        self.candidate: List[Option] = list(candidate) if candidate is not None else []


__all__ = ["Setting", "Option"]
