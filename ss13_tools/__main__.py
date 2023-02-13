#!/env/python3

import traceback
from random import choice
import asyncio
import sys

from colorama import Fore, Style

from .log_downloader import CkeyLogDownloader, RoundLogDownloader


try:
    from .slur_detector import SlurDetector
except FileNotFoundError:
    # Bit of a hack but it does the job
    print(traceback.format_exc().replace("FileNotFoundError:", f"{Fore.RED}FileNotFoundError:") + Fore.RESET)
    print(f"{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
    input()
    sys.exit(1)

colour = choice([Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
                Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
                Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW])

print(f"""Welcome to {colour}ss13-tools{Fore.RESET}! What would you like to do?

{Fore.GREEN}1.{Fore.RESET} Download someone's say history
{Fore.GREEN}2.{Fore.RESET} Run slur detection
{Fore.GREEN}3.{Fore.RESET} All of the above
{Fore.GREEN}4.{Fore.RESET} Download logs from a range of rouds
{Fore.GREEN}5.{Fore.RESET} Run slur search on a range of rounds
{Fore.GREEN}6.{Fore.RESET} Search the CentCom ban database for multiple ckeys at once
""", end='')
choice = input()  # Colorama and input don't mix well :/

try:
    if choice == "1":
        downloader = CkeyLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
    elif choice == "2":
        from .slur_detector import __main__
    elif choice == "3":
        downloader = CkeyLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
        print()  # Newline
        slurs = SlurDetector.from_file(downloader.output_path)
        slurs.print_results()
    elif choice == "4":
        downloader = RoundLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
    elif choice == "5":
        downloader = RoundLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())
        print()  # Newline
        slurs = SlurDetector.from_file(downloader.output_path)
        slurs.print_results()
    elif choice == "6":
        from .centcom import __main__  # noqa: F401
    else:
        print("Invalid choice")
except KeyboardInterrupt:
    sys.exit(0)
except Exception:  # pylint: disable=broad-except
    traceback.print_exc()

print(f"\n{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
input()
