"""Minimal vendored shim of the `songpal` library used by the LSPX-S2 component.

This shim provides lightweight dummies so the custom component can be
installed in Home Assistant without requiring the external `python-songpal`
package. It intentionally implements only minimal interfaces used by the
integration; behaviour is mostly no-op and intended to be replaced by the
real library for production use.
"""

from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional

from .containers import Input, Volume


class SongpalException(Exception):
    def __init__(self, message: str = "", code: Optional[int] = None) -> None:
        super().__init__(message)
        self.code = code


class ConnectChange:
    def __init__(self, exception: Optional[Exception] = None) -> None:
        self.exception = exception


class ContentChange:
    pass


class PowerChange:
    def __init__(self, status: bool = False) -> None:
        self.status = status


class SettingChange:
    pass


class VolumeChange:
    def __init__(self, volume: int = 0, mute: bool = False) -> None:
        self.volume = volume
        self.mute = mute


class Device:
    """Minimal device shim used by the integration.

    Methods are async and return simple placeholders so the integration can
    import and run in Home Assistant. Replace with real implementation for
    actual device control.
    """

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self._handlers: Dict[Any, Callable] = {}
        # State management for settings
        self._lighting_on_off = "on"
        self._lighting_brightness = "20"
        self._led_fluctuation = "off"

    async def get_supported_methods(self) -> None:
        return None

    async def get_interface_information(self) -> SimpleNamespace:
        return SimpleNamespace(modelName="LSPX-S2")

    async def get_system_info(self) -> SimpleNamespace:
        return SimpleNamespace(macAddr=None, wirelessMacAddr=None, version="0")

    async def get_device_misc_settings(self) -> SimpleNamespace:
        """Return device misc settings with proper data structure."""
        # Return structure matching Sony's API response format
        # result[0] is a list of settings with target and currentValue
        return SimpleNamespace(result=[[
            SimpleNamespace(target="lightingOnOff", currentValue=self._lighting_on_off),
            SimpleNamespace(target="lightingBrightness", currentValue=self._lighting_brightness),
            SimpleNamespace(target="ledFluctuationAdjustment", currentValue=self._led_fluctuation),
        ]])

    async def get_sound_settings(self) -> List[Any]:
        return []

    async def get_volume_information(self) -> List[Any]:
        # Return a dummy volume control to allow the media player to initialize
        return [Volume(volume=10, min_volume=0, max_volume=30)]

    async def get_power(self) -> SimpleNamespace:
        return SimpleNamespace(status=False)

    async def get_inputs(self) -> List[Any]:
        # Return a dummy input so media player has at least one source
        return [Input(uri="dummy", title="Input", active=True)]

    async def set_sound_settings(self, name: str, value: Any) -> None:
        return None

    async def set_device_misc_settings(self, settings: List[Dict[str, Any]]) -> None:
        """Update device misc settings from a list of settings."""
        for setting in settings:
            target = setting.get("target")
            value = setting.get("value")
            if target == "lightingOnOff":
                self._lighting_on_off = value
            elif target == "lightingBrightness":
                self._lighting_brightness = str(value)
            elif target == "ledFluctuationAdjustment":
                self._led_fluctuation = value
        return None

    async def set_power(self, on: bool) -> None:
        return None

    async def listen_notifications(self) -> None:
        return None

    async def stop_listen_notifications(self) -> None:
        return None

    def on_notification(self, typ: Any, handler: Callable) -> None:
        self._handlers[typ] = handler


__all__ = [
    "Device",
    "SongpalException",
    "ConnectChange",
    "ContentChange",
    "PowerChange",
    "SettingChange",
    "VolumeChange",
]
