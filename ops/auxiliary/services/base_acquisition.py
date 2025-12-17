import abc
import asyncio
import threading
from logging import getLogger
from typing import Callable

from ops.auxiliary.drivers.measurement import Measurement
from ops.auxiliary.drivers.base import SessionDriver

_log = getLogger(__name__)


def _producer_thread(
    loop: asyncio.AbstractEventLoop, data_queue: asyncio.Queue, producer: Callable[[], Measurement]
):
    _log.info("Producer thread started")
    while True:
        try:
            data = producer()
        except Exception as exc:
            raise RuntimeError(exc)
        loop.call_soon_threadsafe(data_queue.put_nowait, data)


class BaseAquisitionService(abc.ABC):
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._data_queue = asyncio.Queue()

    @abc.abstractmethod
    def _acquire_data(self) -> Measurement:
        raise NotImplementedError

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()

    @property
    def data_queue(self) -> asyncio.Queue:
        return self._data_queue


class SessionDataAcquisition(BaseAquisitionService):
    def __init__(self, driver: SessionDriver) -> None:
        self.driver = driver
        self._is_running = False
        super().__init__()

    async def start(self) -> None:
        await super().start()
        _log.info(f'Starting {self.__class__.__name__} for "{self.driver.__class__.__name__}"...')
        await self.driver.connect()
        self._producer_thread = threading.Thread(
            target=_producer_thread,
            args=(self._loop, self._data_queue, self._acquire_data),
            daemon=True,
            name=f"{self.driver.__class__.__name__} Producer",
        )
        self._producer_thread.start()
        self._is_running = True
        _log.info(f"{self.__class__.__name__} started successfully.")

    async def stop(self):
        if not self._is_running:
            return
        _log.info(f'Stopping {self.__class__.__name__} for "{self.driver.__class__.__name__}"...')
        if self.driver.is_connected:
            _log.debug("Disconnecting...")
            await self.driver.disconnect()
        self._is_running = False
        _log.info("Stopped")
