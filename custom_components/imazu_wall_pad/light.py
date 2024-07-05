"""Light platform for Imazu Wall Pad integration."""

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity, ColorMode
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from wp_imazu.packet import LightPacket, DimmingPacket

from . import ImazuGateway, ImazuWallPadConfigEntry
from .gateway import EntityData
from .wall_pad import WallPadDevice

SCAN_LIGHT_PACKETS = [
    # Light
    "01190140100000",
    "01190140200000",
    "01190140300000",
    "01190140400000",
    "01190140500000",
    "01190140600000",
    # Dimmer
    "011a0142100000",
    "011a0142200000",
    "011a0142300000",
    "011a0142400000",
    "011a0142500000",
    "011a0142600000",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ImazuWallPadConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Imazu Wall Pad config entry."""
    gateway: ImazuGateway = entry.runtime_data

    @callback
    def async_add_entity(entity_data: EntityData):
        if isinstance(entity_data.packet, LightPacket):
            entity_data.device = WPLight(gateway, Platform.LIGHT, entity_data.packet)
            async_add_entities([entity_data.device])
        elif isinstance(entity_data.packet, DimmingPacket):
            entity_data.device = WPDimmer(gateway, Platform.LIGHT, entity_data.packet)
            async_add_entities([entity_data.device])

    entities = gateway.get_platform_entities(Platform.LIGHT)
    for data in entities:
        async_add_entity(data)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, gateway.entity_add_signal(Platform.LIGHT), async_add_entity
        )
    )

    if len(entities) == 0:
        for packet in SCAN_LIGHT_PACKETS:
            await gateway.async_send(bytes.fromhex(packet))


class WPLight(WallPadDevice[LightPacket], LightEntity):
    """Representation of a Wall Pad light."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.packet.state["power"] == LightPacket.Power.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        make_packet = self.packet.make_change_power(LightPacket.Power.ON)
        await super().async_send_packet(make_packet)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        make_packet = self.packet.make_change_power(LightPacket.Power.OFF)
        await super().async_send_packet(make_packet)


class WPDimmer(WallPadDevice[DimmingPacket], LightEntity):
    """Representation of a Wall Pad light."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return (
            "brightness" in self.packet.state and self.packet.state["brightness"] != 0
        )

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        if "brightness" not in self.packet.state:
            return 0
        return round(self.packet.state["brightness"] * 255 / 3)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = round(kwargs[ATTR_BRIGHTNESS] * 3 / 255)
            make_packet = self.packet.make_change_brightness(brightness)
        else:
            make_packet = self.packet.make_change_brightness(3)

        await super().async_send_packet(make_packet)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        make_packet = self.packet.make_change_brightness(0)
        await super().async_send_packet(make_packet)
