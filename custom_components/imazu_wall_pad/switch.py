"""Switch platform for Imazu Wall Pad integration."""

import logging
from typing import Any

from wp_imazu.packet import GasPacket, OutletPacket

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import ImazuGateway, ImazuWallPadConfigEntry
from .gateway import EntityData
from .wall_pad import WallPadDevice

_LOGGER = logging.getLogger(__name__)

SCAN_SWITCH_PACKETS = [
    "011f0140100000",
    "011f0140200000",
    "011f0140300000",
    "011f0140400000",
    "011f0140500000",
    "011f0140600000",
    "011b0143110000",
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
        if isinstance(entity_data.packet, OutletPacket):
            entity_data.device = WPOutlet(gateway, Platform.SWITCH, entity_data.packet)
            async_add_entities([entity_data.device])
        elif isinstance(entity_data.packet, GasPacket):
            entity_data.device = WPGasValve(
                gateway, Platform.SWITCH, entity_data.packet
            )
            async_add_entities([entity_data.device])

    entities = gateway.get_platform_entities(Platform.SWITCH)
    for data in entities:
        async_add_entity(data)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, gateway.entity_add_signal(Platform.SWITCH), async_add_entity
        )
    )

    if len(entities) == 0:
        for packet in SCAN_SWITCH_PACKETS:
            await gateway.async_send(bytes.fromhex(packet))


class WPOutlet(WallPadDevice[OutletPacket], SwitchEntity):
    """Representation of a Wall Pad switch."""

    _attr_icon = "mdi:power-socket-eu"

    @property
    def device_class(self) -> SwitchDeviceClass:
        """Return the class of this entity."""
        return SwitchDeviceClass.OUTLET

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.packet.state["power"] == OutletPacket.Power.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on switch."""
        make_packet = self.packet.make_change_power(OutletPacket.Power.ON)
        await super().async_send_packet(make_packet)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off switch."""
        make_packet = self.packet.make_change_power(OutletPacket.Power.OFF)
        await super().async_send_packet(make_packet)


class WPGasValve(WallPadDevice[GasPacket], SwitchEntity):
    """Representation of a Wall Pad gas valve."""

    @property
    def device_class(self) -> SwitchDeviceClass:
        """Return the class of this entity."""
        return SwitchDeviceClass.SWITCH

    @property
    def is_on(self) -> bool:
        """Return true if gas valve is open."""
        return self.packet.state["valve"] == GasPacket.Valve.OPEN

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Can not be opened remotely."""
        _LOGGER.warning("The gas valve cannot be opened remotely")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off gas valve."""
        make_packet = self.packet.make_change_valve_close()
        await super().async_send_packet(make_packet)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return "mdi:valve-open" if self.is_on else "mdi:valve-closed"
