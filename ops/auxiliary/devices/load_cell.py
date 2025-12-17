from logging import getLogger
from typing import Optional

from ops.auxiliary.drivers.voltage_ratio_bridge import VoltageRatioBridge
from .base import _LogicalDeviceBase

_log = getLogger(__name__)


class LoadCell(_LogicalDeviceBase):
    def __init__(
        self,
        connection: VoltageRatioBridge,
        read_key: VoltageRatioBridge.Channel,
        name: str = "Load cell",
        gain: Optional[float] = None,
        offset: Optional[float] = None,
    ):
        super().__init__(connection)
        self._read_key = read_key
        self._gain = gain
        self._offset = offset
        self._name = name

    async def calibrate(self) -> None:
        try:
            _log.info(f"Calibrating {self._name}, clear load cell and press Enter")
            input()
        except KeyboardInterrupt:
            _log.info("Calibration aborted.")
            return

        v1 = await self._connection.read_data(self._read_key)

        try:
            _log.info(
                f"Place a known weight on {self._name}, type the weight in grams and press Enter:"
            )
            w2 = input("> ")
        except KeyboardInterrupt:
            _log.info("Calibration aborted.")
            return

        v2 = await self._connection.read_data(self._read_key)
        self._gain = float(w2) / (v2 - v1)
        self._offset = -self._gain * v1

        _log.info(f"Calibration complete, gain = {self._gain:0.4f}, offset = {self._offset:0.4f}")

    async def read_weight(self) -> float:
        if self._gain is None or self._offset is None:
            raise RuntimeError("Load cell not calibrated")
        return self._gain * (await self._connection.read_data(self._read_key)) + self._offset
