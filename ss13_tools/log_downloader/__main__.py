from .constants import DEFAULT_ONLY_PLAYED, DEFAULT_OUTPUT_PATH, DEFAULT_NUMBER_OF_ROUNDS
# TODO: soon
# from .downloader import LogDownloader

import sys

from colorama import Fore

# Do argparse
if 2 < len(sys.argv) < 6:
    ckey = sys.argv[1]
    number_of_rounds = int(sys.argv[2])
    output_path = DEFAULT_OUTPUT_PATH.format(ckey=ckey)
    if len(sys.argv) > 3:
        output_path = sys.argv[3]
    only_played = DEFAULT_ONLY_PLAYED
    if len(sys.argv) > 4:
        only_played = sys.argv[4]
        raise NotImplementedError()
    # LogDownloader(ckey, number_of_rounds, output_path, only_played)
elif len(sys.argv) != 1:
    print(f"{Fore.YELLOW}Unknown number of command line arguments{Fore.RESET}")
    print(f"{Fore.GREEN}USAGE{Fore.RESET}: candy-stalker.py <ckey> [number_of_rounds={DEFAULT_NUMBER_OF_ROUNDS}]" +
          "[output_path={ckey}.txt] [only_played=false]")
    print("<> are required, [] are optional, = means a default value. If you provide an optional, you have to also " +
          "provide all optionals before it")
    exit(1)
else:
    # LogDownloader.interactive()
    raise NotImplementedError()
