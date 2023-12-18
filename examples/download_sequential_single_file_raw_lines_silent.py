# flake8: noqa
# pylint: skip-file

import asyncio

from ss13_tools.log_downloader import RoundLogDownloader


async def main():
    downloader = RoundLogDownloader(200000, 200010)  # Sequential
    downloader.files = ["game.log", "attack.log"]
    downloader.output_only_log_line = True  # Does not format the file whatsoever, just outputs raw lines
    downloader.silent = True  # No output
    downloader.try_authenticate_interactive()  # To access raw logs, remove if you're accessing only parsed logs
    downloader.process_and_write("outfile.txt")

asyncio.run(main())
