import asyncio
from enum import Enum, auto
from logging import getLogger
from typing import Optional, List, Dict

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput

from .base import SessionDriver

_log = getLogger(__name__)


class VoltageRatioBridge(SessionDriver):
    class Channel(Enum):
        CHANNEL_0 = auto()
        CHANNEL_1 = auto()
        CHANNEL_2 = auto()
        CHANNEL_3 = auto()

    def __init__(self, channels_to_connect: Optional[List[Channel]] = None) -> None:
        if channels_to_connect is None:
            channels_to_connect = [ch for ch in VoltageRatioBridge.Channel]
        self._bridge_channels: Dict[VoltageRatioBridge.Channel, VoltageRatioInput] = {
            channel: VoltageRatioInput() for channel in channels_to_connect
        }

    @property
    def is_connected(self) -> bool:
        for channel in self._bridge_channels.values():
            if not channel.getIsOpen():
                return False
        return True

    def channel_is_connected(self, channel: Channel) -> bool:
        return self._bridge_channels[channel].getIsOpen()

    async def connect(self) -> None:
        if self.is_connected:
            _log.debug("Voltage ratio bridge is already connected")
        else:
            _log.info("Connecting to bridge channels...")
            for channel, bridge in self._bridge_channels.items():
                _log.debug(f"{channel} is already connected...")
                if self.channel_is_connected(channel):
                    continue
                _log.debug(f"Connecting {channel}...")
                await asyncio.to_thread(self._bridge_channels[channel].openWaitForAttachment, 3000)
        if not self.is_connected:
            raise ConnectionError("Failed to connect bridge")
        _log.info("Bridge channels connected.")

    async def disconnect(self) -> None:
        if not self.is_connected:
            _log.debug("Voltage raitio bridge is already disconnected")
            return
        _log.info("Disconnecting voltage ratio bridge")
        for channel, bridge in self._bridge_channels.items():
            if self.channel_is_connected(channel):
                await asyncio.to_thread(bridge.close)
        _log.info("Bridge disconnected")
