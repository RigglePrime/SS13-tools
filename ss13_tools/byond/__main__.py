from colorama import Fore, Style

from .key_tools import user_exists


def main():
    """Main"""
    try:
        print("Paste ckeys to search for, one per line (press CTRL + C to stop)\n")
        while True:
            key = input('> ')
            exists = user_exists(key)
            print(Fore.GREEN if exists else Fore.RED, end='')
            print(f"{Style.BRIGHT}{key}{Style.NORMAL}", "exists" if exists else "does not exist", Fore.RESET)
    except KeyboardInterrupt:
        print("Bye!")


if __name__ == "__main__":
    main()
