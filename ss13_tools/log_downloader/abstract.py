"""Abstract implementation of a log downloader"""

import asyncio
from abc import ABC, abstractmethod
from typing import Generator, Iterable, Annotated, Union

from aiohttp import ClientSession
from colorama import Fore
from dateutil.parser import isoparse
from tqdm.asyncio import tqdm

from .constants import DEFAULT_OUTPUT_PATH
from ..constants import USER_AGENT
from ..scrubby import RoundData


class LogDownloader(ABC):
    """Log downloader object. For downloading logs.
    Either pass the arguments in the constructor or call `interactive()`"""

    tgforums_cookie: Annotated[str, "Forum cookie if you want raw logs"] = ""
    user_agent: Annotated[str, "User agent so people know who keeps spamming requests (and for raw logs)"] = USER_AGENT
    output_path: Annotated[str, "Where should we write the file to?"] = DEFAULT_OUTPUT_PATH
    rounds: Annotated[list[RoundData], "The list of rounds to download"] = []

    @abstractmethod
    def get_rounds(self) -> list[RoundData]:
        """Gets the specified rounds we want to download"""

    @abstractmethod
    def get_log_links(self, round_data: RoundData) -> Iterable[str]:
        """Gets the links of logs we want to download"""

    @abstractmethod
    def filter_lines(self, logs):
        """Filters lines from a log file, returning only the ones we want"""

    @abstractmethod
    def interactive(self) -> None:
        """Interactively set variables"""

    async def get_logs_async(self, rounds: Iterable[RoundData])\
            -> Generator[tuple[RoundData, Union[list[bytes], None]], None, None]:
        """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`

        if `output_bytes` is true, the function will instead yield `bytes` instead of `str`

        On 404, the list will be None instead"""
        async with ClientSession(cookies={"tgforums_sid": self.tgforums_cookie},
                                 headers={"User-Agent": self.user_agent}) as session:
            tasks = []
            # url_to_use = GAME_TXT_URL

            async def fetch(round_data: RoundData):
                round_data.timestamp = isoparse(round_data.timestamp)
                responses = []
                for link in self.get_log_links(round_data):
                    # Edge case warning: if we go beyond the year 2017 or so, the logs path changes.
                    # I don't expect anyone to go that far so I won't be doing anything about it
                    async with session.get(link) as r:
                        if not r.ok:
                            continue
                        responses.append(await r.read())
                    return round_data, b'\r\n'.join(responses)

            # if self.tgforums_cookie and self.user_agent:
            #     url_to_use = GAME_TXT_ADMIN_URL
            #     round_data, response = await fetch(rounds[0])
            #     if not response:
            #         print(f"{Fore.RED}ERROR: The cookie and user agent were set but invalid,",
            #               f"reverting to normal logs.{Fore.RESET}")
            #         url_to_use = GAME_TXT_URL

            for round_data in rounds:
                tasks.append(asyncio.ensure_future(fetch(round_data=round_data)))

            for task in tasks:
                round_data, response = await task
                response: bytes
                if not response:
                    yield round_data, None
                else:
                    yield round_data, response.split(b"\r\n")

            await asyncio.gather(*tasks)

    @staticmethod
    def format_line_bytes(line: bytes, round_data: RoundData) -> list[str]:
        """Takes the raw line and formats it to `{server_name} {round_id} | {unmodified line}`"""
        return round_data.server.encode("utf-8") + b" " + str(round_data.roundID).encode("utf-8") + b" | " + line + b"\n"

    async def process_and_write(self, output_path: str = None):
        """In progress"""
        output_path = output_path or self.output_path
        with open(output_path, 'wb') as file:
            pbar = tqdm(self.get_logs_async(self.rounds))
            async for round_data, logs in pbar:
                # Type hints
                round_data: RoundData
                logs: list[bytes]

                pbar.set_description(f"Getting ID {round_data.roundID} on {round_data.server}")
                if not logs:
                    pbar.clear()
                    print(f"{Fore.YELLOW}WARNING:{Fore.RESET} Could not find round " +
                          f"{round_data.roundID} on {round_data.server}")
                    pbar.display()
                    continue
                if round_data.roundStartSuicide:
                    pbar.clear()
                    print(f"{Fore.MAGENTA}WARNING:{Fore.RESET} round start suicide " +
                          f"in round {round_data.roundID} on {round_data.server}")
                    pbar.display()
                for line in self.filter_lines(logs):
                    file.write(self.format_line_bytes(line, round_data))
