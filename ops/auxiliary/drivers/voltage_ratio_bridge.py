import asyncio
from enum import Enum, auto
from logging import getLogger
from typing import Any, Optional, List, Dict

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException


from .base import SessionDriver

_log = getLogger(__name__)


class VoltageRatioBridge(SessionDriver):
    class Channel(Enum):
        CHANNEL_0 = auto()
        CHANNEL_1 = auto()
        CHANNEL_2 = auto()
        CHANNEL_3 = auto()

    CHANNEL_MAPPING = {
        Channel.CHANNEL_0: 0,
        Channel.CHANNEL_1: 1,
        Channel.CHANNEL_2: 2,
        Channel.CHANNEL_3: 3,
    }

    def __init__(self, channels_to_connect: Optional[List[Channel]] = None) -> None:
        if channels_to_connect is None:
            channels_to_connect = [ch for ch in VoltageRatioBridge.Channel]
        self._bridge_channels: Dict[VoltageRatioBridge.Channel, VoltageRatioInput] = {
            channel: VoltageRatioInput() for channel in channels_to_connect
        }
        for channel, input in self._bridge_channels.items():
            input.setChannel(VoltageRatioBridge.CHANNEL_MAPPING[channel])
        self._connection_lock = asyncio.Lock()

    async def read_data(self, data_key: Channel) -> float:
        if not self.channel_is_connected(data_key):
            raise ConnectionError("Cannot read, channel is not connected")
        return await asyncio.to_thread(self._bridge_channels[data_key].getVoltageRatio)

    async def write_data(self, data_key: Any, value: float) -> None:
        raise NotImplementedError("Cannot write to voltage ratio bridge")

    @property
    def is_connected(self) -> bool:
        for channel in self._bridge_channels.values():
            if not channel.getIsOpen():
                return False
        return True

    def channel_is_connected(self, channel: Channel) -> bool:
        try:
            return self._bridge_channels[channel].getIsOpen()
        except KeyError:
            return False

    async def connect(self) -> None:
        if self.is_connected:
            _log.debug("Voltage ratio bridge is already connected")
        else:
            _log.info("Connecting to bridge channels...")
            for channel, bridge in self._bridge_channels.items():
                async with self._connection_lock:
                    if self.channel_is_connected(channel):
                        _log.debug(f"{channel} is already connected...")
                        continue
                    _log.debug(f"Connecting {channel}...")
                    try:
                        await asyncio.to_thread(
                            self._bridge_channels[channel].openWaitForAttachment, 5000
                        )
                    except PhidgetException:
                        raise ConnectionError(f"Failed to connect to channel {channel}")
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
