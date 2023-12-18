# flake8: noqa
# pylint: skip-file

import asyncio

from ss13_tools.log_downloader import RoundLogDownloader
from ss13_tools.log_downloader.base import RoundResource


async def main():
    downloader = RoundLogDownloader(200000, 200010)  # Sequential
    downloader.files = ["game.log", "attack.log"]
    downloader.authenticate("TOKEN_HERE")  # To access raw logs, remove if you're accessing only parsed logs

    async for round_data, logs in await downloader.get_log_async_iterator_async():
        round_data: RoundResource
        logs: list[bytes]

        print(f"Processing {round_data.round_id} on {round_data.server}")

        if not logs:
            # Could not get logs from that round!
            continue

        with open(f"{round_data.round_id}-{round_data.file_name}.txt", "wb") as f:
            f.writelines(line + b'\n' for line in logs)

asyncio.run(main())
