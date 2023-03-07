#!/env/python3

import traceback
from random import choice
import sys

from colorama import Fore, Style

from ss13_tools.menu import MenuItem  # Absolute import because of pyinstaller
from ss13_tools.constants import __version__


colour = choice([Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
                Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
                Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW])

print(f"\033[38;5;243mVersion {__version__}{Fore.RESET}")
print(f"Welcome to {colour}ss13-tools{Fore.RESET}! What would you like to do?")
classes = {str(i): x for i, x in enumerate(sorted(x() for x in MenuItem.__subclasses__()), 1)}

for key, value in classes.items():
    print(f"{Fore.GREEN}{key}{Fore.RESET}: {value.description}")

try:
    choice = input()  # Colorama and input don't mix well :/
    classes[choice].run()
except KeyError:
    print("Invalid choice")
except KeyboardInterrupt:
    sys.exit(0)
except Exception:  # pylint: disable=broad-except
    traceback.print_exc()

print(f"\n{Style.DIM}Press return to exit...{Style.RESET_ALL}", end='')
input()
