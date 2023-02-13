from colorama import Fore, Style

from .key_tools import user_exists


try:
    print("Paste ckeys to search for, one per line (press CTRL + C to stop)\n")
    while True:
        key = input()
        EXISTS = user_exists(key)
        print(Fore.GREEN if EXISTS else Fore.RED, end='')
        print(f"{Style.BRIGHT}{key}{Style.NORMAL}", "exists" if EXISTS else "does not exist", Fore.RESET)
except KeyboardInterrupt:
    print("Bye!")
