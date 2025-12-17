import asyncio
import time

from ops.auxiliary.devices.load_cell import LoadCell
from .base_acquisition import SessionDataAcquisition
from ops.auxiliary.drivers.measurement import ValueMeasurement
from ops.auxiliary.drivers.base import SessionDriver


class LoadCellAquisitionService(SessionDataAcquisition):
    def __init__(self, load_cell: LoadCell, update_interval: float = 1.0) -> None:
        if not isinstance(load_cell._connection, SessionDriver):
            raise ValueError("Aquisition must be via a session driver")
        super().__init__(load_cell._connection)
        self.load_cell = load_cell
        self.update_interval = update_interval

    def _acquire_data(self) -> ValueMeasurement:
        coroutine = self.load_cell.read_weight()
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        data = future.result()
        data_time = time.time()
        time.sleep(self.update_interval)
        return ValueMeasurement(source=self.load_cell._id, timestamp=data_time, value=data)
