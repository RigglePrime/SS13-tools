# flake8: noqa
# pylint: skip-file

import asyncio

from ss13_tools.log_downloader import RoundLogDownloader
from ss13_tools.log_downloader.base import RoundResource
from tqdm.asyncio import tqdm


async def main():
    downloader = RoundLogDownloader(200000, 200010)  # Sequential
    downloader.files = ["game.log", "attack.log"]
    downloader.try_authenticate_interactive()  # To access raw logs, remove if you're accessing only parsed logs

    async for round_data, logs in tqdm(await downloader.get_log_async_iterator_async(), total=len(downloader.round_resources)):
        round_data: RoundResource
        logs: list[bytes]

        print(f"Processing {round_data.round_id} on {round_data.server}")

        if not logs:
            # Could not get logs from that round!
            continue

        with open(f"{round_data.round_id}-{round_data.file_name}", "wb") as f:
            f.writelines(line + b'\n' for line in logs)

asyncio.run(main())
