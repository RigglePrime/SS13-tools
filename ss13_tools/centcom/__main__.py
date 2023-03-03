from colorama import Fore

from ss13_tools.centcom.ban import get_one


def main():
    """Main"""
    try:
        print("Paste ckeys to search for, one per line (press CTRL + C to stop)\n")
        while True:
            key = input('> ')
            if not key:
                print("Enter a ckey, or CTRL+C to stop")
                continue
            ban_data = get_one(key)

            print(f"{key}:\n")
            if len(ban_data) == 0:
                print("No data")
            for ban in ban_data:
                print(f"{Fore.CYAN}{ban.sourceName}, {ban.sourceRoleplayLevel} RP{Fore.RESET}")
                print(f"Banned on {ban.bannedOn} by {Fore.BLUE}{ban.bannedBy}{Fore.RESET}")
                print("With reason:", ban.reason)
                print("Expires:", ban.expires or f"{Fore.RED}never{Fore.RESET}", "and is",
                      f"{Fore.RED}active{Fore.RESET}" if ban.active else f"{Fore.GREEN}not active{Fore.RESET}")
            print("=========================\n")
    except KeyboardInterrupt:
        print("Bye!")


if __name__ == "__main__":
    main()
