"""Support for LSPX-S2 device lighting (projector lighting)."""

from __future__ import annotations

import logging
from typing import Any

from .songpal import SongpalException

from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up LSPX-S2 light (if supported by device)."""
    # Import here to allow test patching
    from .media_player import Device

    name = entry.data.get("name") or entry.data.get(CONF_ENDPOINT)
    endpoint = entry.data[CONF_ENDPOINT]

    device = Device(endpoint)

    # Check whether the device exposes misc settings API required for lighting
    if not hasattr(device, "get_device_misc_settings") or not hasattr(
        device, "set_device_misc_settings"
    ):
        _LOGGER.debug(
            "Device %s does not support device misc settings, skipping light", endpoint
        )
        return

    light = LspxLight(name, device)
    async_add_entities([light], True)


class LspxLight(LightEntity):
    """Representation of an LSPX-S2 lighting control."""

    _attr_should_poll = True

    def __init__(self, name: str, device: Any) -> None:
        """Initialize the LSPX-S2 light entity."""
        self._name = name
        self._dev = device
        self._is_on = False
        self._brightness = 0
        self._available = False
        self._unique_id = None

    @property
    def name(self) -> str:
        """Return the name of the light."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return self._is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""
        return self._available

    @property
    def unique_id(self) -> str | None:
        """Return unique ID derived from device MAC address."""
        return self._unique_id

    async def async_update(self) -> None:
        """Update the light state from device."""
        try:
            # Device API for device misc settings commonly returns a
            # structure with a result list of settings. We attempt to read
            # targets used by Sony projectors: lightingOnOff, lightingBrightness,
            # ledFluctuationAdjustment
            data = await self._dev.get_device_misc_settings()

            # Fetch unique ID from system info on first update if not already set
            if self._unique_id is None:
                try:
                    sysinfo = await self._dev.get_system_info()
                    self._unique_id = getattr(sysinfo, "macAddr", None) or getattr(
                        sysinfo, "wirelessMacAddr", None
                    )
                except Exception:
                    pass

            # Reset defaults
            self._is_on = False
            self._brightness = 0

            # Parse result structure defensively
            # Expecting data.result[0] is iterable of items with target/currentValue
            result = getattr(data, "result", None)
            if not result:
                self._available = True
                return

            items = result[0]
            for item in items:
                target = getattr(item, "target", None)
                cur = getattr(item, "currentValue", None)
                if target == "lightingOnOff":
                    self._is_on = cur == "on"
                elif target == "lightingBrightness":
                    try:
                        self._brightness = int(cur) * 255 // 32
                    except Exception:
                        pass
                elif target == "ledFluctuationAdjustment":
                    # If candle (fluctuation) mode is on we treat brightness
                    # as low/1% and as on
                    if cur == "on":
                        self._is_on = True
                        self._brightness = max(1, int(255 * 0.01))

            self._available = True

        except SongpalException as ex:
            _LOGGER.debug("Failed to get device misc settings: %s", ex)
            self._available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the lighting on. Supports optional brightness."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        try:
            if brightness is not None:
                # Map HA brightness (0-255) to device scale (0-32)
                device_brightness = max(0, round(brightness / 255 * 32))
                await self._dev.set_device_misc_settings([
                    {"target": "lightingBrightness", "value": str(device_brightness)}
                ])
                # Ensure candle mode is off for explicit brightness
                await self._dev.set_device_misc_settings([
                    {"target": "ledFluctuationAdjustment", "value": "off"}
                ])
            else:
                # Simple on: try to set lightingOnOff on
                await self._dev.set_device_misc_settings([
                    {"target": "lightingOnOff", "value": "on"}
                ])
            # Reflect optimistic state until next update
            self._is_on = True
            if brightness is not None:
                self._brightness = brightness
            self.async_write_ha_state()
        except SongpalException as ex:
            _LOGGER.error("Failed to turn on lighting: %s", ex)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the lighting off."""
        try:
            # Turn off both regular lighting and candle mode
            await self._dev.set_device_misc_settings([
                {"target": "ledFluctuationAdjustment", "value": "off"},
                {"target": "lightingOnOff", "value": "off"},
            ])
            self._is_on = False
            self.async_write_ha_state()
        except SongpalException as ex:
            _LOGGER.error("Failed to turn off lighting: %s", ex)
