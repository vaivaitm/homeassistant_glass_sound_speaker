"""Support for LSPX-S2 sound settings."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, service

from .const import DOMAIN

PARAM_NAME = "name"
PARAM_VALUE = "value"

SET_SOUND_SETTING = "set_sound_setting"


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services."""
    service.async_register(
        hass,
        DOMAIN,
        SET_SOUND_SETTING,
        schema={
            vol.Required(PARAM_NAME): cv.string,
            vol.Required(PARAM_VALUE): cv.string,
        },
    )
