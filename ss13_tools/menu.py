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
        from .slur_detector.__main__ import main
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
    description = "Download logs from a range of rounds"

    def run(self):
        downloader = RoundLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())


class RoundAndSlurItem(MenuItem):
    name = "round slur detector"
    description = "Run slur detection on a range of rounds"

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
        from .centcom.__main__ import main
        main()


class UserExistsItem(MenuItem):
    name = "BYOND user exists"
    description = "Check if users on a list exist or not"

    def run(self):
        from .byond.__main__ import main
        main()


class TokenTestServiceItem(MenuItem):
    name = "Token test service"
    description = "The one-stop shop for TG13 token testing"

    def run(self):
        from .auth.__main__ import main
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
        from .log_buddy.__main__ import main
        main()


class RoundListDownloaderItem(MenuItem):
    name = "Round list downloader"
    description = "Download a comma separated list of rounds"

    def run(self):
        downloader = RoundListLogDownloader.interactive()
        asyncio.run(downloader.process_and_write())


class SuspiciousAccessDownloaderItem(MenuItem):
    name = "Suspicious downloader"
    description = "Downloads a range of suspicious access logs"

    def run(self):
        from .auth.tg import interactive as interactive_auth
        print("Input boundry rounds, separated by a space: ")
        while True:
            rounds = input("> ").split(' ', 1)
            if len(rounds) != 2:
                print("Please input two rounds.")
                continue
            if rounds[0].isnumeric() and rounds[1].isnumeric():
                break
            print("Those don't seem to be numbers, please try again")
        downloader = RoundLogDownloader(int(rounds[0]), int(rounds[1]))
        downloader.files = ["suspicious_logins.log"]
        downloader.silent = True
        interactive_auth()
        asyncio.run(downloader.process_and_write())


class JobCounterItem(MenuItem):
    name = "Job counter"
    description = "Display what jobs someone played"

    def run(self):
        from .scrubby import GetReceipts, ScrubbyException
        ckey = input("Ckey: ")
        while True:
            try:
                number_of_rounds = int(input("How many rounds? "))
                break
            except ValueError:
                print("That doesn't seem to be a number...")
        try:
            receipts = asyncio.run(GetReceipts(ckey, number_of_rounds, True))
        except ScrubbyException:
            print("Seems like that ckey couldn't be found! Check your spelling and try again")
            return

        print("Calculating...")
        from collections import Counter
        number_of_rounds = len(receipts)
        print(f"Out of {Fore.GREEN}{number_of_rounds}{Fore.RESET} last round{'s' if number_of_rounds != 1 else ''} " +
              f"{Fore.GREEN}{ckey}{Fore.RESET} played in, they played the following jobs:\n")
        for job, count in Counter(x.job for x in receipts).items():
            print(f"{job:>24}:    {count / number_of_rounds * 100:05.2f}% ({count})")
        antag = sum(x.antagonist for x in receipts)
        suicide = sum(x.roundStartSuicide for x in receipts)
        # roller = sum(x.roundStartSuicide and x.antagonist for x in receipts)
        print(f"\nOut of those, they were an antagonist {antag / number_of_rounds * 100:.2f}% " +
              f"of the time ({antag} round{'s' if antag != 1 else ''}), and round-start suicided " +
              f"{suicide} time{'s' if suicide != 1 else ''}.")
        # if roller:
        #     print(f"{Fore.RED}Out of those {suicide} suicides, they got an antagonist " +
        #           f"{roller} time{'s' if suicide != 1 else ''}!{Fore.RESET}")
        # else:
        #     print(f"{Fore.GREEN}They never round-start suicided and got antagonist.{Fore.RESET}")


# Commented out because it sucked too much.
# class TextSimilarityItem(MenuItem):
#     name = "Text similarity"
#     description = "Determine how similarly two people tend to type"

#     def run(self):
#         from .util import jaccard_similarity
#         from .byond import user_exists, canonicalize
#         print(f"{Fore.YELLOW}This uses a metric called Jaccard similarity. Results may vary.{Fore.RESET}")
#         while True:
#             ckey1 = canonicalize(input("Ckey 1: "))
#             if user_exists(ckey1):
#                 break
#             print(f"{ckey1} does not seem to exist, try again?")
#         while True:
#             ckey2 = canonicalize(input("Ckey 2: "))
#             if user_exists(ckey2):
#                 break
#             print(f"{ckey2} does not seem to exist, try again?")
#         from .log_buddy import LogFile, LogType
#         downloader = CkeyLogDownloader(ckey1, only_played=True, number_of_rounds=20)
#         downloader.files = ["game.txt"]
#         downloader.filter_logs = True
#         downloader.output_only_log_line = True
#         asyncio.run(downloader.process_and_write())
#         log_file = LogFile.from_file(downloader.output_path)
#         log_file.filter_ckeys(ckey1)
#         log_file.filter_by_type([LogType.SAY])
#         person1_words = []
#         for log in log_file.logs:
#             person1_words.extend(log.text.split())
#         downloader = CkeyLogDownloader(ckey2, only_played=True, number_of_rounds=20)
#         downloader.files = ["game.txt"]
#         downloader.filter_logs = True
#         downloader.output_only_log_line = True
#         asyncio.run(downloader.process_and_write())
#         log_file = LogFile.from_file(downloader.output_path)
#         log_file.filter_ckeys(ckey2)
#         log_file.filter_by_type([LogType.SAY])
#         person2_words = []
#         for log in log_file.logs:
#             person2_words.extend(log.text.split())
#         del log_file

#         print(f"\n{Fore.GREEN}Jaccard similarity index:",
#               jaccard_similarity(person1_words, person2_words),
#               Fore.RESET)
