"""Binary Sensor platform for Imazu Wall Pad integration."""

from wp_imazu.packet import AwayPacket, ImazuPacket

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from imazu_wall_pad import ImazuGateway, ImazuWallPadConfigEntry
from .const import BRAND_NAME
from .gateway import EntityData
from .helper import host_to_last
from .wall_pad import WallPadDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ImazuWallPadConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Imazu Wall Pad config entry."""
    gateway: ImazuGateway = entry.runtime_data

    @callback
    def async_add_entity(entity_data: EntityData):
        if isinstance(entity_data.packet, AwayPacket):
            if "power" in entity_data.packet.state:
                entity_data.device = WPAwayLight(
                    gateway, Platform.BINARY_SENSOR, entity_data.packet
                )
                async_add_entities([entity_data.device])
            elif "valve" in entity_data.packet.state:
                entity_data.device = WPAwayGasValve(
                    gateway, Platform.BINARY_SENSOR, entity_data.packet
                )
                async_add_entities([entity_data.device])

    entities = gateway.get_platform_entities(Platform.BINARY_SENSOR)
    for data in entities:
        async_add_entity(data)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, gateway.entity_add_signal(Platform.BINARY_SENSOR), async_add_entity
        )
    )


class WPAwayLight(WallPadDevice[AwayPacket], BinarySensorEntity):
    """Representation of a Wall Pad away light."""

    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(
        self, gateway: ImazuGateway, platform: Platform, packet: ImazuPacket
    ) -> None:
        """Set up binary_sensor."""
        super().__init__(gateway, platform, packet)

        self._attr_should_poll = False

        self.entity_id = (
            f"{str(platform.value)}."
            f"{BRAND_NAME}_{host_to_last(self.gateway.host)}_"
            f"{self.packet.name.lower()}_light_{packet.room_id}"
        )
        self._attr_name = f"{BRAND_NAME} {packet.name} Light {packet.room_id}".title()

    @property
    def is_on(self) -> bool:
        """Return true if away light is on."""
        return self.packet.state["power"] == AwayPacket.Power.ON

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return "mdi:lightbulb-group" if self.is_on else "mdi:lightbulb-group-outline"


class WPAwayGasValve(WallPadDevice[AwayPacket], BinarySensorEntity):
    """Representation of a Wall Pad away gas valve."""

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self, gateway: ImazuGateway, platform: Platform, packet: ImazuPacket
    ) -> None:
        """Set up binary_sensor."""
        super().__init__(gateway, platform, packet)

        self._attr_should_poll = False

        self.entity_id = (
            f"{str(platform.value)}."
            f"{BRAND_NAME}_{host_to_last(self.gateway.host)}_"
            f"{self.packet.name.lower()}_gas_{packet.room_id}"
        )
        self._attr_name = f"{BRAND_NAME} {packet.name} Gas {packet.room_id}".title()

    @property
    def is_on(self) -> bool:
        """Return true if gas valve is open."""
        return self.packet.state["valve"] == AwayPacket.Valve.OPEN

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return "mdi:valve-open" if self.is_on else "mdi:valve-closed"
