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


class Volume:
    """Dummy volume control object."""
    
    def __init__(self, volume: int = 10, min_volume: int = 0, max_volume: int = 30, muted: bool = False) -> None:
        self.volume = volume
        self.minVolume = min_volume
        self.maxVolume = max_volume
        self.is_muted = muted

    async def set_volume(self, volume: int) -> None:
        """Set volume."""
        self.volume = max(self.minVolume, min(volume, self.maxVolume))

    async def set_mute(self, mute: bool) -> None:
        """Set mute state."""
        self.is_muted = mute


class Input:
    """Dummy input/source object."""
    
    def __init__(self, uri: str = "", title: str = "", active: bool = False) -> None:
        self.uri = uri
        self.title = title
        self.active = active

    async def activate(self) -> None:
        """Activate this input."""
        self.active = True


__all__ = ["Setting", "Option", "Volume", "Input"]
