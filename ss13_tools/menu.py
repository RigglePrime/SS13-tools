"""
This file contains the menu items that should be loaded into the main menu.
All of them must inherit from MenuItem
"""
# pylint: disable=missing-class-docstring,too-few-public-methods,import-outside-toplevel
import asyncio
import traceback
import sys

from colorama import Style, Fore

from .menu_item import MenuItem
from .constants import POSITIVE_RESPONSES
from .log_downloader import CkeyLogDownloader, RoundLogDownloader, RoundListLogDownloader

try:
    from .slur_detector import SlurDetector
except FileNotFoundError:
    # Bit of a hack but it does the job
    print(traceback.format_exc().replace("FileNotFoundError:", f"{Fore.RED}FileNotFoundError:") + Fore.RESET)
    print(f"{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
    input()
    sys.exit(1)


class CkeySingleItem(MenuItem):
    weight = 2
    name = "ckey log downloader"
    description = "Download someone's say history (and more!)"

    def run(self):
        downloader = CkeyLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())


class SlurDetectorSingleItem(MenuItem):
    name = "slur detector"
    description = "Run slur detection on a file"

    def run(self):
        from .slur_detector import main
        main()


class CkeyAndSlurItem(MenuItem):
    weight = 3
    name = "ckey log slur detector"
    description = "Run slur detection on someone's say logs"

    def run(self):
        downloader = CkeyLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
        print()  # Newline
        slurs = SlurDetector.from_file(downloader.output_path)
        slurs.print_results()


class RoundSingleItem(MenuItem):
    weight = 4
    name = "round log downloader"
    description = "Download logs from a range of rouds"

    def run(self):
        downloader = RoundLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())


class RoundAndSlurItem(MenuItem):
    name = "round slur detector"
    description = "Run slur detector on a range of rouds"

    def run(self):
        downloader = RoundLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
        print()  # Newline
        slurs = SlurDetector.from_file(downloader.output_path)
        slurs.print_results()


class CentComItem(MenuItem):
    name = "CentCom"
    description = "Search the CentCom ban database for ckeys"

    def run(self):
        from .centcom import main
        main()


class UserExistsItem(MenuItem):
    name = "BYOND user exists"
    description = "Check if users on a list exist or not"

    def run(self):
        from .byond import main
        main()


class TokenTestServiceItem(MenuItem):
    name = "Token test service"
    description = "The one-stop shop for TG13 token testing"

    def run(self):
        from .auth import main
        main()


class PlayedTogetherItem(MenuItem):
    name = "Rounds played together"
    description = "Tells you the rounds two (or more) people have all played in"

    def run(self):  # noqa: C901
        while True:
            try:
                number_of_rounds = int(input("How many rounds? "))
                break
            except ValueError:
                print("That doesn't seem to be a number...")

        from .scrubby import GetReceipts, ScrubbyException
        print("Please enter the desired ckeys. Leave empty to stop")
        receipts_collection = []
        ckeys = []
        while ckey := input():
            try:
                ckeys.append(ckey)
                receipts = asyncio.run(GetReceipts(ckey, number_of_rounds, False))
                receipts_collection.append(receipts)
            except ScrubbyException:
                print("Seems like that ckey couldn't be found! Check your spelling and try again")
        print("Calculating...")
        round_set = set(rd.roundID for rd in receipts_collection[0])
        if len(receipts_collection) == 1:
            print("Seems like there's only one person here, here's the rounds they played in:")
            print(', '.join(str(x) for x in round_set))
            return

        for receipts in receipts_collection[1:]:
            round_set = round_set & set(rd.roundID for rd in receipts)

        print("Here are your stats:")
        print("I looked for the ckeys", ', '.join(ckeys))
        print(f"Out of {number_of_rounds} rounds, they played " +
              f"{Fore.GREEN}{len(round_set) / number_of_rounds * 100}%{Fore.RESET} together")
        print(f"Those rounds were:{Fore.GREEN}", ', '.join(str(x) for x in round_set) or "none!", Fore.RESET)

        if not round_set:
            return
        print(f"Would you like to download these rounds? [y/{Style.BRIGHT}N{Style.NORMAL}] ", end="")
        if not input().strip() in POSITIVE_RESPONSES:
            return
        downloader = RoundListLogDownloader(round_set)
        downloader.try_authenticate_interactive()
        asyncio.run(downloader.process_and_write())
        print("Saved as", downloader.output_path)


class LogBuddyItem(MenuItem):
    weight = 1
    name = "LogBuddy"
    description = "Run LogBuddy"

    def run(self):
        from .log_buddy import main
        main()


class RoundListDownloaderItem(MenuItem):
    name = "Round list downloader"
    description = "Download a comma separated list of rounds"

    def run(self):
        downloader = RoundListLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
