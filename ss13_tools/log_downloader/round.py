from typing import Annotated, Iterable

from dateutil.parser import isoparse

from .base import LogDownloader, RoundResource
from .constants import DEFAULT_FILES, DEFAULT_ROUND_LIST_OUTPUT_PATH, DEFAULT_ROUND_OUTPUT_PATH
from ..scrubby.RoundController import get_round_info_from_ids


class RoundLogDownloader(LogDownloader):
    """Downloads a span of rounds"""
    lbound: Annotated[int, "Left boundary"]
    rbound: Annotated[int, "Right boundary"]

    def __init__(self, start_round: int, end_round: int, output_path: str = None) -> None:
        super().__init__()
        self.lbound = min(start_round, end_round)
        self.rbound = max(start_round, end_round)
        self.output_path = output_path or DEFAULT_ROUND_OUTPUT_PATH.format(start=self.lbound, end=self.rbound)

    async def _update_round_list(self) -> None:
        def round_list_generator():
            i = self.lbound
            while i <= self.rbound:
                yield i
                i += 1
        async for round_info in get_round_info_from_ids(round_list_generator()):
            round_info.timestamp = isoparse(round_info.timestamp)
            for file_name in self.files:
                self.round_resources.append(RoundResource(
                    round_id=round_info.round_id,
                    timestamp=round_info.timestamp,
                    server=round_info.server,
                    file_name=file_name
                ))

    def _filter_lines(self, logs: list[bytes]) -> Iterable[bytes]:
        return logs

    @staticmethod
    def interactive() -> LogDownloader:
        while True:
            try:
                start = int(input("First round: "))
                break
            except ValueError:
                print("Could not parse that as a number, please try again")
        while True:
            try:
                end = int(input("Last round (inclusive): "))
                break
            except ValueError:
                print("Could not parse that as a number, please try again")
        output_path = input("Where should I write the file? " +
                            f"[{DEFAULT_ROUND_OUTPUT_PATH.format(start=start, end=end)}] ")
        downloader = RoundLogDownloader(start, end, output_path)
        print("Which files do you want to download?")
        print("(separate the files with a comma, like so: attack.txt,game.txt,pda.txt)")
        file_list = [x.strip() for x in input(f"[{','.join(DEFAULT_FILES)}] ").split(',') if x.strip()]
        if file_list:
            downloader.files = file_list
        downloader.try_authenticate_interactive()
        return downloader


class RoundListLogDownloader(LogDownloader):
    """Downloads a span of rounds"""
    round_list: Annotated[Iterable[int], "List of rounds to get"]

    def __init__(self, round_list: Iterable[int], output_path: str = None) -> None:
        super().__init__()
        self.round_list = round_list
        self.output_path = output_path or DEFAULT_ROUND_LIST_OUTPUT_PATH

    async def _update_round_list(self) -> None:
        async for round_info in get_round_info_from_ids(self.round_list):
            round_info.timestamp = isoparse(round_info.timestamp)
            for file_name in self.files:
                self.round_resources.append(RoundResource(
                    round_id=round_info.round_id,
                    timestamp=round_info.timestamp,
                    server=round_info.server,
                    file_name=file_name
                ))

    def _filter_lines(self, logs: list[bytes]) -> Iterable[bytes]:
        return logs

    @staticmethod
    def interactive() -> LogDownloader:
        while True:
            try:
                round_list = input("Input round IDs, separated by commas or spaces: ")
                sep = ',' if ',' in round_list else ' '
                round_list = (int(x) for x in round_list.split(sep))
                break
            except ValueError:
                print("Could not parse a number, please try again")
        output_path = input(f"Where should I write the file? [{DEFAULT_ROUND_OUTPUT_PATH}] ")
        downloader = RoundListLogDownloader(round_list, output_path)
        print("Which files do you want to download?")
        print("(separate the files with a comma, like so: attack.txt,game.txt,pda.txt)")
        file_list = [x.strip() for x in input(f"[{','.join(DEFAULT_FILES)}] ").split(',') if x.strip()]
        if file_list:
            downloader.files = file_list
        downloader.try_authenticate_interactive()
        return downloader
