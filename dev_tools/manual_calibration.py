import asyncio
import logging
from ops.auxiliary.drivers.voltage_ratio_bridge import VoltageRatioBridge

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
_log = logging.getLogger("ops")


async def calibrate():
    channels = [VoltageRatioBridge.Channel.CHANNEL_0, VoltageRatioBridge.Channel.CHANNEL_3]

    bridge = VoltageRatioBridge(channels_to_connect=channels)
    await bridge.connect()


if __name__ == "__main__":
    asyncio.run(calibrate())
