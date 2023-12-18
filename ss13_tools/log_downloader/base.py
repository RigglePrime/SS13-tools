"""Abstract implementation of a log downloader"""
from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from typing import Generator, Iterable, Annotated, Union
from dataclasses import dataclass
from datetime import datetime
import re

from aiohttp import ClientSession
from colorama import Fore, Style
from tqdm.asyncio import tqdm

from .constants import DEFAULT_OUTPUT_PATH, ROUND_FILES_URL, ROUND_FILES_ADMIN_URL, DEFAULT_FILES
from ..constants import USER_AGENT, POSITIVE_RESPONSES, NEGATIVE_RESPONSES
from ..auth import is_authenticated, create_from_token, interactive as tgauth_interactive, get_auth_headers, seconds_left


@dataclass
class RoundResource():
    """Represent a round resource (file) that is to be downloaded"""
    round_id: int
    timestamp: datetime
    server: str
    file_name: str

    def get_round_url(self, url_format: str = ROUND_FILES_URL) -> str:
        """Gets the url for this resource"""
        return url_format.format(
            server=self.server,
            year=str(self.timestamp.year),
            month=f"{self.timestamp.month:02d}",
            day=f"{self.timestamp.day:02d}",
            round_id=self.round_id,
            file_name=self.file_name
        )


class LogDownloader(ABC):
    """Log downloader object. For downloading logs.
    Either pass the arguments in the constructor or call `interactive()`"""

    user_agent: Annotated[str, "User agent so people know who keeps spamming requests (and for raw logs)"]
    output_path: Annotated[str, "Where should we write the file to?"]
    round_resources: Annotated[list[RoundResource], "The list of round resoruces to download"]
    files: Annotated[list[str], "Which files do we want to dowload?"]
    output_only_log_line: Annotated[bool, "Should we format our line or not?"]
    silent: Annotated[bool, "Should we be quiet?"]
    __authed: Annotated[bool, "Are we authenticated?"]

    def __init__(self) -> None:
        self.user_agent = USER_AGENT
        self.output_path = DEFAULT_OUTPUT_PATH
        self.round_resources = []
        self.files = DEFAULT_FILES.copy()
        self.output_only_log_line = False
        self.silent = False
        self.__authed = False

    def authenticate(self, token: str, override_old: bool = False) -> bool:
        """Tries to authenticate against the TG forums"""
        if is_authenticated():
            return True
        return create_from_token(token=token, override_old=override_old)

    def try_authenticate_interactive(self) -> bool:
        """Tries to authenticate against the TG forums interactively"""
        if is_authenticated() and seconds_left() < 30:
            print(f"{Fore.YELLOW}WARNING{Fore.RESET}: token has less than 30 seconds left")
            print(f"Refresh the token? [{Style.BRIGHT}Y{Style.NORMAL}/n] ", end='')
            if input().lower() not in NEGATIVE_RESPONSES:
                while not create_from_token(input("Token: ").strip(), True):
                    pass  # There's a print if Passport errors on creation. Terrible code. Future me will fix it.
                return True
        print(f"Would you like to access raw logs? [y/{Style.BRIGHT}N{Style.NORMAL}] ", end='')
        if input().lower() not in POSITIVE_RESPONSES:
            return False
        return tgauth_interactive()

    @abstractmethod
    async def _update_round_list(self) -> None:  # Not the best way of doing it but I can't be bothered right now
        """Generates a list of rounds and saves it to self.rounds"""

    @abstractmethod
    def _filter_lines(self, logs: list[bytes]) -> Iterable[bytes]:
        """Filters lines from a log file, returning only the ones we want"""

    async def __get_logs_async(self) -> Generator[tuple[RoundResource, Union[list[bytes], None]], None, None]:
        """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`

        if `output_bytes` is true, the function will instead yield `bytes` instead of `str`

        On 404, the list will be None instead"""
        headers = {"User-Agent": self.user_agent}
        if self.__authed:
            headers.update(get_auth_headers())
            url_format = ROUND_FILES_ADMIN_URL
        else:
            url_format = ROUND_FILES_URL
        async with ClientSession(headers=headers) as session:
            tasks = []

            async def fetch(round_resource: RoundResource):
                # Edge case warning: if we go beyond the year 2017 or so, the logs path changes.
                # I don't expect anyone to go that far so I won't be doing anything about it
                async with session.get(round_resource.get_round_url(url_format=url_format)) as rsp:
                    if not rsp.ok:
                        return round_resource, None
                    return round_resource, await rsp.read()

            for round_resource in self.round_resources:
                tasks.append(asyncio.ensure_future(fetch(round_resource)))

            # This could be out of order but we don't really care, it's not important
            for task in tasks:
                response: bytes
                round_resource, response = await task
                if not response:
                    yield round_resource, None
                else:
                    yield round_resource, re.split(rb"\r?\n", response)
            await asyncio.gather(*tasks)

    @staticmethod
    def _format_line_bytes(line: bytes, round_data: RoundResource) -> bytes:
        """Takes the raw line and formats it to `{server_name} {round_id} | {unmodified line}`"""
        if not line:
            return b''
        return round_data.server.capitalize().encode("utf-8").rjust(6, b' ') + \
            b" " + str(round_data.round_id).encode("utf-8") + b" | " + line + b"\n"

    @staticmethod
    def _output_raw_line(line: bytes, _) -> bytes:
        """Returns the line right back"""
        return line + b"\n"

    async def get_log_async_iterator_async(self, force_resource_update: bool = False):
        """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`

        Parameters:
        `force_resource_update` (bool): should we force an updated round resource list? This is not necessary
        unless the round data changed since last time we processed it

        On 404, the logs will be None instead"""
        if force_resource_update or not self.round_resources:
            if is_authenticated():
                self.__authed = True
                self.files = [file.replace(".txt", ".log") for file in self.files]
            else:
                self.__authed = False
                self.files = [file.replace(".log", ".txt") for file in self.files]
            await self._update_round_list()
        return self.__get_logs_async()

    async def get_logs_list_async(self, force_resource_update: bool = False):
        """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`

        Parameters:
        `force_resource_update` (bool): should we force an updated round resource list? This is not necessary
        unless the round data changed since last time we processed it

        On 404, the round file will be skipped"""
        return [(round_data, logs) async for round_data, logs
                in await self.get_log_async_iterator_async(force_resource_update=force_resource_update) if logs]

    async def process_and_write(self, output_path: str = None):
        """Processes the data, downloads the logs and saves them to a file"""
        output_path = output_path or self.output_path
        formatter = self._output_raw_line if self.output_only_log_line else self._format_line_bytes

        with open(output_path, 'wb') as file:
            pbar = tqdm(await self.get_log_async_iterator_async(), total=len(self.round_resources))
            async for round_data, logs in pbar:
                # Type hints
                round_data: RoundResource
                logs: list[bytes]

                pbar.set_description(f"Getting ID {round_data.round_id} on {round_data.server.capitalize()}")
                if not logs:
                    if not self.silent:
                        pbar.clear()
                        print(f"{Fore.YELLOW}WARNING:{Fore.RESET} Could not get {round_data.file_name} " +
                              f"from round {round_data.round_id} on {round_data.server.capitalize()}")
                        pbar.display()
                    continue
                for line in self._filter_lines(logs):
                    file.write(formatter(line, round_data))

    @staticmethod
    @abstractmethod
    def interactive() -> LogDownloader:
        """Interactively set variables"""
