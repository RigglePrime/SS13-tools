from typing import Annotated, Iterable

from .abstract import LogDownloader
from .constants import DEFAULT_FILES, DEFAULT_ROUND_LIST_OUTPUT_PATH, DEFAULT_ROUND_OUTPUT_PATH
from ..scrubby.RoundController import round_ids_to_round_data


class RoundLogDownloader(LogDownloader):
    """Downloads a span of rounds"""
    lbound: Annotated[int, "Left boundary"]
    rbound: Annotated[int, "Right boundary"]

    def __init__(self, start_round: int, end_round: int, output_path: str = None) -> None:
        self.lbound = min(start_round, end_round)
        self.rbound = max(start_round, end_round)
        self.output_path = output_path or DEFAULT_ROUND_OUTPUT_PATH.format(start=self.lbound, end=self.rbound)

    async def _update_round_list(self) -> None:
        def round_list_generator():
            i = self.lbound
            while i <= self.rbound:
                yield i
                i += 1
        async for round_data in round_ids_to_round_data(round_list_generator()):
            self.rounds.append(round_data)

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
        output_path = input(f"Where should I write the file? [{DEFAULT_ROUND_OUTPUT_PATH}] ")
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
    round_list: Annotated[list[int], "List of rounds to get"]

    def __init__(self, round_list, output_path: str = None) -> None:
        self.round_list = round_list
        self.output_path = output_path or DEFAULT_ROUND_LIST_OUTPUT_PATH

    async def _update_round_list(self) -> None:
        async for round_data in round_ids_to_round_data(self.round_list):
            self.rounds.append(round_data)

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
