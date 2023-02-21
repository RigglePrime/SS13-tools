"""
This file contains the menu items that should be loaded into the main menu.
All of them must inherit from MenuItem
"""
# pylint: disable=missing-class-docstring,too-few-public-methods
import asyncio
import traceback
import sys

from colorama import Style, Fore

from .menu_item import MenuItem
from .log_downloader import CkeyLogDownloader, RoundLogDownloader

try:
    from .slur_detector import SlurDetector
except FileNotFoundError:
    # Bit of a hack but it does the job
    print(traceback.format_exc().replace("FileNotFoundError:", f"{Fore.RED}FileNotFoundError:") + Fore.RESET)
    print(f"{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
    input()
    sys.exit(1)


class CkeySingleItem(MenuItem):
    weight = 1
    name = "ckey log downloader"
    description = "Download someone's say history"

    def run(self):
        downloader = CkeyLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())


class SlurDetectorSingleItem(MenuItem):
    name = "slur detector"
    description = "Run slur detection on a file"

    def run(self):
        from .slur_detector import main  # pylint: disable=import-outside-toplevel
        main()


class CkeyAndSlurItem(MenuItem):
    weight = 2
    name = "ckey log slur detector"
    description = "Run slur detection on someone's say logs"

    def run(self):
        downloader = CkeyLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
        print()  # Newline
        slurs = SlurDetector.from_file(downloader.output_path)
        slurs.print_results()


class RoundSingleItem(MenuItem):
    weight = 3
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
        from .centcom import main  # pylint: disable=import-outside-toplevel
        main()


class UserExistsItem(MenuItem):
    name = "BYOND user exists"
    description = "Check if users on a list exist or not"

    def run(self):
        from .byond import main  # pylint: disable=import-outside-toplevel
        main()
