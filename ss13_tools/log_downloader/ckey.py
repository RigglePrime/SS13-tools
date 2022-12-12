from typing import Annotated, Optional

from colorama import Fore, Style

from .abstract import LogDownloader
from .constants import DEFAULT_NUMBER_OF_ROUNDS, DEFAULT_ONLY_PLAYED, DEFAULT_OUTPUT_PATH
from ..byond import canonicalize


class CkeyLogDownloader(LogDownloader):
    """Downloads logs in which a ckey was present"""
    ckey: Annotated[Optional[str], "Canonical form of user's key, can be None"]
    only_played: Annotated[bool, "If ckey is set dictates if the log downloader only counts player rounds"]\
        = DEFAULT_ONLY_PLAYED
    number_of_rounds: Annotated[int, "The number of rounds to download"] = DEFAULT_NUMBER_OF_ROUNDS
    output_path: Annotated[str, "Where should we write the file to?"] = DEFAULT_OUTPUT_PATH.format(ckey="output")

    def __init__(self, key: str = None, only_played: bool = DEFAULT_ONLY_PLAYED,
                 number_of_rounds: int = DEFAULT_NUMBER_OF_ROUNDS, output_path: str = None) -> None:
        self.ckey = canonicalize(key) if key else None
        self.only_played = only_played
        self.number_of_rounds = number_of_rounds
        self.output_path = output_path.format(ckey=self.ckey or "output")

    def interactive(self) -> None:
        """Run interactive mode. Returns the choices and runs default behaviour
        Sets the correct variables automatically.`"""
        self.ckey = input("CKEY: ").strip()
        while True:
            number_of_rounds = input(f"How many rounds? [{DEFAULT_NUMBER_OF_ROUNDS}] ")
            try:
                if not number_of_rounds.strip():
                    break
                self.number_of_rounds = int(number_of_rounds) if number_of_rounds.isdigit() else int(number_of_rounds, 16)
                break
            except ValueError:
                print(f"{Fore.RED}Rounds should be an int in base 10 or 16{Fore.RESET}")
        print(f"Do you want to get only rounds in which they played? [y/{Style.BRIGHT}N{Style.RESET_ALL}] ", end="")
        only_played = input()  # Input and colorama don't mix
        if only_played:
            self.only_played = True if only_played.lower() == 'y' or 'yes' or 'true' or '1' else False
        output_path = input(f"Where should I write the file? [{DEFAULT_OUTPUT_PATH}] ")
        self.output_path = output_path or DEFAULT_OUTPUT_PATH.format(ckey=self.ckey)
