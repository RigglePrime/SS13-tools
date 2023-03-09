import sys
import asyncio

from colorama import Fore

from .constants import DEFAULT_ONLY_PLAYED, DEFAULT_CKEY_OUTPUT_PATH, DEFAULT_NUMBER_OF_ROUNDS
from . import CkeyLogDownloader, RoundLogDownloader
from .base import LogDownloader


def make_ckey_downloader() -> LogDownloader:
    """Tries to construct a ckey downloader from args"""
    ckey = sys.argv[2]
    number_of_rounds = int(sys.argv[3])
    output_path = DEFAULT_CKEY_OUTPUT_PATH.format(ckey=ckey)
    if len(sys.argv) > 4:
        output_path = sys.argv[4]
    only_played = DEFAULT_ONLY_PLAYED
    if len(sys.argv) > 5:
        only_played = sys.argv[5]
        raise NotImplementedError()
    return CkeyLogDownloader(ckey, number_of_rounds, output_path, only_played)


def make_round_id_downloader() -> LogDownloader:
    """Tries to construct a round id downloader from args"""
    file_path = sys.argv[4] if len(sys.argv) == 4 else f"{sys.argv[1]}-{sys.argv[2]}"
    return RoundLogDownloader(int(sys.argv[2]), int(sys.argv[3]), file_path)


def print_help():
    """Prints the help text"""
    print(f"{Fore.YELLOW}Unknown number of command line arguments{Fore.RESET}")
    print(f"{Fore.GREEN}USAGE{Fore.RESET}: {sys.argv[0]} ckey <ckey> [number_of_rounds={DEFAULT_NUMBER_OF_ROUNDS}]" +
          "[output_path={ckey}.txt] [only_played=false]")
    print(f"{Fore.GREEN}USAGE{Fore.RESET}: {sys.argv[0]} round <start_round> <end_round> [output_path]")
    print("<> are required, [] are optional, = means a default value. If you provide an optional, you have to also " +
          "provide all optionals before it")


# Do argparse
if 2 < len(sys.argv) < 7:
    if sys.argv[1] == "round":
        downloader = make_round_id_downloader()
    elif sys.argv[1] == "ckey":
        downloader = make_ckey_downloader()
    else:
        print_help()
        sys.exit(1)
elif len(sys.argv) != 1:
    print_help()
    sys.exit(1)
else:
    downloader = CkeyLogDownloader()
    downloader.interactive()
    asyncio.run(downloader.process_and_write())
