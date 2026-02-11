"""Minimal vendored shim of the `songpal` library used by the LSPX-S2 component.

This shim provides lightweight dummies so the custom component can be
installed in Home Assistant without requiring the external `python-songpal`
package. It intentionally implements only minimal interfaces used by the
integration; behaviour is mostly no-op and intended to be replaced by the
real library for production use.
"""

import json
import logging
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

from .containers import Input, Volume

_LOGGER = logging.getLogger(__name__)


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
        self.endpoint = endpoint.removesuffix("/sony")
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
        """Return device misc settings with proper data structure.
        
        Fetches from actual device if available, otherwise returns local state.
        """
        # Try to fetch from actual device
        if aiohttp is not None:
            try:
                payload = {
                    "method": "getDeviceMiscSettings",
                    "id": 1,
                    "params": [{"target": ""}],
                    "version": "1.0"
                }
                
                url = self.endpoint.rstrip("/") + "/sony/system"
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            # Parse the response and update internal state
                            if "result" in data and data["result"]:
                                result_list_of_dicts = data["result"][0]
                                if isinstance(result_list_of_dicts, list):
                                    # Update internal state for fallback
                                    for item in result_list_of_dicts:
                                        target = item.get("target")
                                        value = item.get("currentValue")
                                        if target == "lightingOnOff":
                                            self._lighting_on_off = value
                                        elif target == "lightingBrightness":
                                            self._lighting_brightness = str(value)
                                        elif target == "ledFluctuationAdjustment":
                                            self._led_fluctuation = value
                                    # Convert dicts to SimpleNamespaces for the caller
                                    result_list_of_ns = [
                                        SimpleNamespace(**d)
                                        for d in result_list_of_dicts
                                    ]
                                    return SimpleNamespace(result=[result_list_of_ns])
                                # Fallback for non-list result, though not expected
                                return SimpleNamespace(result=data.get("result", [[]]))
                        else:
                            _LOGGER.debug(
                                "Failed to get device settings from %s: HTTP %d",
                                url,
                                resp.status
                            )
            except Exception as ex:
                _LOGGER.debug("Error fetching device settings: %s", ex)
        
        # Return local state structure  
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
        """Update device misc settings from a list of settings.
        
        This method both updates the local state and sends the settings to the actual device
        via HTTP JSON-RPC request.
        """
        # Update local state for immediate reflection
        for setting in settings:
            target = setting.get("target")
            value = setting.get("value")
            if target == "lightingOnOff":
                self._lighting_on_off = value
            elif target == "lightingBrightness":
                self._lighting_brightness = str(value)
            elif target == "ledFluctuationAdjustment":
                self._led_fluctuation = value
        
        # Send to actual device if aiohttp is available
        if aiohttp is None:
            _LOGGER.debug("aiohttp not available, skipping device update")
            return
        
        try:
            # Build JSON-RPC request
            payload = {
                "method": "setDeviceMiscSettings",
                "id": 1,
                "params": [{"settings": settings}],
                "version": "1.0"
            }
            
            # Determine URL from endpoint
            # endpoint is typically like http://192.168.0.54:54480
            # the actual endpoint is /sony/system
            url = self.endpoint.rstrip("/") + "/sony/system"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.warning(
                            "Failed to set device misc settings on %s: HTTP %d",
                            url,
                            resp.status
                        )
                    else:
                        _LOGGER.debug("Successfully set device settings: %s", settings)
        except Exception as ex:
            _LOGGER.warning("Error setting device misc settings: %s", ex)

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
