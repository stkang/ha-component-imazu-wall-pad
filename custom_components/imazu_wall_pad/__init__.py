"""The Imazu Wall Pad integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant
from imazu_wall_pad.custom_components.imazu_wall_pad.const import DOMAIN, PLATFORMS
from imazu_wall_pad.custom_components.imazu_wall_pad.gateway import ImazuGateway

type ImazuWallPadConfigEntry = ConfigEntry[ImazuGateway]  # noqa: F821


async def async_setup_entry(
    hass: HomeAssistant, entry: ImazuWallPadConfigEntry
) -> bool:
    """Set up Imazu Wall Pad from a config entry."""
    imazu_gateway = ImazuGateway(hass, entry)
    await imazu_gateway.async_load_entity_registry()

    if not await imazu_gateway.async_connect():
        await imazu_gateway.async_close()
        return False

    entry.runtime_data = imazu_gateway
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await imazu_gateway.async_close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        imazu_gateway = entry.runtime_data
        await imazu_gateway.async_close()

    return unload_ok
