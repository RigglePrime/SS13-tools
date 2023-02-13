from .ban import get_one


try:
    print("Paste ckeys to search for, one per line (press CTRL + C to stop)\n")
    while True:
        key = input()
        ban_data = get_one(key)

        print(f"{key}:\n")
        if len(ban_data) == 0:
            print("No data")
        for ban in ban_data:
            print(ban.sourceName, ban.sourceRoleplayLevel)
            print(f"Banned on {ban.bannedOn} by {ban.bannedBy}")
            print("With reason:", ban.reason)
            print("Expires:", ban.expires or "never", "and is", "active" if ban.active else "not active")
        print("=========================\n")
except KeyboardInterrupt:
    print("Bye!")
