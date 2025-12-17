import asyncio
import logging
from ops.auxiliary.drivers.measurement import ValueMeasurement
from ops.auxiliary.drivers.voltage_ratio_bridge import VoltageRatioBridge
from ops.auxiliary.devices.load_cell import LoadCell
from ops.auxiliary.services.load_cell import LoadCellAquisitionService

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
_log = logging.getLogger("ops")

Channel = VoltageRatioBridge.Channel


async def broadcast_data(queue: asyncio.Queue):
    while True:
        data: ValueMeasurement = await queue.get()
        print(f"{data.source} weight:{data.value:>30.0f}")
        queue.task_done()


async def calibrate():
    channels = [Channel.CHANNEL_0, Channel.CHANNEL_3]
    bridge = VoltageRatioBridge(channels_to_connect=channels)

    load_cell_0 = LoadCell(bridge, Channel.CHANNEL_0, id="Load cell, channel 0")
    await load_cell_0.connect()
    load_cell_3 = LoadCell(bridge, Channel.CHANNEL_3, id="Load cell, channel 3")
    await load_cell_3.connect()

    await load_cell_0.calibrate()
    await load_cell_3.calibrate()

    load_cell_0_service = LoadCellAquisitionService(load_cell_0, 1.0)
    load_cell_3_service = LoadCellAquisitionService(load_cell_3, 1.0)

    try:
        _log.info("Starting services...")
        await load_cell_0_service.start()
        await load_cell_3_service.start()
        _log.info("All services running.")

        tasks = [
            broadcast_data(load_cell_0_service._data_queue),
            broadcast_data(load_cell_3_service._data_queue),
        ]
        _log.info("Application is running. Press Ctrl+C to exit")
        await asyncio.gather(*tasks)

    except (KeyboardInterrupt, asyncio.CancelledError):
        _log.info("Shutdown signal received...")
    except Exception:
        _log.exception("An unknown exception occurred, shutting down...")
    finally:
        _log.info("Cleaning up resources...")
        await asyncio.gather(
            load_cell_0_service.stop(), load_cell_3_service.stop(), return_exceptions=True
        )
        _log.info("Cleanup complete. Exiting.")


if __name__ == "__main__":
    asyncio.run(calibrate())
