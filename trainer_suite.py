#!/env/python3

import traceback
from random import choice
from candy_stalker import interactive

from colorama import Fore, Style, init as colorama_init
colorama_init()

try:
    from slur_detector.slur_detector import SlurDetector
except FileNotFoundError:
    # Bit of a hack but it does the job
    print(traceback.format_exc().replace("FileNotFoundError:", f"{Fore.RED}FileNotFoundError:") + Fore.RESET)
    print(f"{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
    input()
    exit(1)

colour = choice([Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
                Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
                Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW])

print(f"""Welcome to {colour}trainer suite{Fore.RESET}! What would you like to do?

{Fore.GREEN}1.{Fore.RESET} Download someone's say history
{Fore.GREEN}2.{Fore.RESET} Run slur detection
{Fore.GREEN}3.{Fore.RESET} All of the above
{Fore.GREEN}4.{Fore.RESET} Run slur search on a range of rounds
{Fore.GREEN}5.{Fore.RESET} Search the CentCom ban database for multiple ckeys at once
""", end='')
choice = input()  # Colorama and input don't mix well :/

try:
    if choice == "1":
        interactive()
    elif choice == "2":
        SlurDetector.from_file(input("Which file? ")).print_results()
    elif choice == "3":
        ckey, number_of_rounds, output_path, only_played = interactive()
        print()
        slurs = SlurDetector.from_file(output_path)
        slurs.print_results()
    elif choice == "4":
        print("Not yet implemented")
    elif choice == "5":
        from centcom import __main__  # noqa: F401
    else:
        print("Invalid choice")
except KeyboardInterrupt:
    exit(0)
except Exception:
    traceback.print_exc()

print(f"\n{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
input()
