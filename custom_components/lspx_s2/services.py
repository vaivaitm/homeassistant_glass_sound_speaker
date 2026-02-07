"""Support for LSPX-S2 sound settings."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

PARAM_NAME = "name"
PARAM_VALUE = "value"

SET_SOUND_SETTING = "set_sound_setting"


async def async_set_sound_setting(hass: HomeAssistant, call) -> None:
    """Handle set sound setting service call."""
    # Service handler - can be extended with actual device control logic
    pass


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services."""
    hass.services.async_register(
        DOMAIN,
        SET_SOUND_SETTING,
        async_set_sound_setting,
        schema=vol.Schema({
            vol.Required(PARAM_NAME): cv.string,
            vol.Required(PARAM_VALUE): cv.string,
        }),
    )
