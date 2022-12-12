from .constants import DEFAULT_OUTPUT_PATH
from ..constants import USER_AGENT
from scrubby import RoundData

from abc import ABC, abstractclassmethod
from typing import Generator, Iterable, Annotated, Union

from aiohttp import ClientSession
import asyncio
from colorama import Fore
from dateutil.parser import isoparse
from tqdm.asyncio import tqdm


class LogDownloader(ABC):
    """Log downloader object. For downloading logs.
    Either pass the arguments in the constructor or call `interactive()`"""

    tgforums_cookie: Annotated[str, "Forum cookie if you want raw logs"] = ""
    user_agent: Annotated[str, "User agent so people know who keeps spamming requests (and for raw logs)"] = USER_AGENT
    output_path: Annotated[str, "Where should we write the file to?"] = DEFAULT_OUTPUT_PATH
    rounds: Annotated[list[RoundData], "The list of rounds to download"] = []

    @abstractclassmethod
    def get_rounds(self):
        pass

    @abstractclassmethod
    def get_log_links(self, round_data: RoundData) -> Iterable[str]:
        pass

    @abstractclassmethod
    def filter_lines(self):
        pass

    @abstractclassmethod
    def interactive(self) -> None:
        pass

    async def get_logs_async(self, rounds: Iterable[RoundData])\
            -> Generator[tuple[RoundData, Union[list[bytes], None]], None, None]:
        """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`

        if `output_bytes` is true, the function will instead yield `bytes` instead of `str`

        On 404, the list will be None instead"""
        async with ClientSession(cookies={"tgforums_sid": self.tgforums_cookie},
                                 headers={"User-Agent": self.user_agent}) as session:
            tasks = []
            # url_to_use = GAME_TXT_URL

            async def fetch(round: RoundData):
                round.timestamp = isoparse(round.timestamp)
                responses = []
                for link in self.get_log_links(round):
                    # Edge case warning: if we go beyond the year 2017 or so, the logs path changes.
                    # I don't expect anyone to go that far so I won't be doing anything about it
                    async with session.get(link) as r:
                        if not r.ok:
                            continue
                        responses.append(await r.read())
                    return round, b'\r\n'.join(responses)

            # if self.tgforums_cookie and self.user_agent:
            #     url_to_use = GAME_TXT_ADMIN_URL
            #     round, response = await fetch(rounds[0])
            #     if not response:
            #         print(f"{Fore.RED}ERROR: The cookie and user agent were set but invalid,",
            #               f"reverting to normal logs.{Fore.RESET}")
            #         url_to_use = GAME_TXT_URL

            for round in rounds:
                tasks.append(asyncio.ensure_future(fetch(round=round)))

            for task in tasks:
                round, response = await task
                response: bytes
                if not response:
                    yield round, None
                else:
                    yield round, response.split(b"\r\n")

            await asyncio.gather(*tasks)

    def format_line_bytes(line: bytes, round: RoundData) -> list[str]:
        """Takes the raw line and formats it to `{server_name} {round_id} | {unmodified line}`"""
        return round.server.encode("utf-8") + b" " + str(round.roundID).encode("utf-8") + b" | " + line + b"\n"

    async def process_and_write(self, output_path: str = None):
        output_path = output_path or self.output_path
        with open(output_path, 'wb') as f:
            pbar = tqdm(self.get_logs_async(self.rounds))
            async for round, logs in pbar:
                # Type hints
                round: RoundData
                logs: list[bytes]

                pbar.set_description(f"Getting ID {round.roundID} on {round.server}")
                if not logs:
                    pbar.clear()
                    print(f"{Fore.YELLOW}WARNING:{Fore.RESET} Could not find round {round.roundID} on {round.server}")
                    pbar.display()
                    continue
                if round.roundStartSuicide:
                    pbar.clear()
                    print(f"{Fore.MAGENTA}WARNING:{Fore.RESET} round start suicide in round {round.roundID} on {round.server}")
                    pbar.display()
                for line in self.filter_lines(logs):
                    f.write(self.format_line_bytes(line, round))
