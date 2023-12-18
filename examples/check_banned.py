"""Checks if any players in a toolbox tournament team are permabanned."""

# flake8: noqa
# pylint: skip-file

import json

from ss13_tools.byond import user_exists
from ss13_tools.centcom import get_one

with open("toolbox_teams.json", encoding="utf-8") as f:
    toolbox_teams = json.load(f)

checked_players = []
banned_players = []
problem_teams = []
valid_teams = []

print("Teams:", len(toolbox_teams))
for team in toolbox_teams:
    valid = True
    print("Team {}:".format(team["name"]))
    for player in team["roster"]:
        player: str = player.strip()
        print("Checking {}...".format(player), end='')
        if not player:
            print(" ERROR! no name!")
            valid = False
            continue
        if player in checked_players:  # Two teams can't have the same player
            print(" WARNING! Player in two teams!")
            valid = False
            continue
        if not user_exists(player):  # Check if user exists
            print(" WARNING! Player does not exist!")
            problem_teams.append(team["name"])
            valid = False
            continue
        ban_data = get_one(player)
        if ban_data == None:  # Getting none means we got an error
            print(" ERROR! Got 404")
            valid = False
            continue
        if len(ban_data) == 0:  # All good!
            print(" clean!")
            continue
        is_banned = False
        for ban in ban_data:  # We got some ban data, check it
            ban_value = bool(ban.expires) + ban.active + ban.type == "Server"
            if ban_value == 0:
                print(".", end="")
            elif ban_value == 1:
                print("*", end='')
            elif ban_value == 2:
                print("○", end='')
            elif ban_value == 3:
                print("@", end='')
            # (ban.sourceID == 9) == (ban.sourceName == "/tg/station")
            if not ban.expires and ban.active and ban.type == "Server" and ban.sourceID == 9:
                banned_players.append(player)
                problem_teams.append(team["name"])
                print(" banned!", end='')
                is_banned = True
                valid = False
        if not is_banned:
            print(" clean", end='')
        print()  # newline
    if valid:
        valid_teams.append(team["name"])
    print()

print("Banned:")
print(banned_players)
print()
problem_teams = set(problem_teams)
print("Problematic:")
print(problem_teams)
print()
print(f"Valid ({len(valid_teams)}):")
print(valid_teams)
print()

# Sanity
for team in toolbox_teams:
    name = team["name"]
    if name not in problem_teams and name not in valid_teams:
        print(f"{name} is orphaned!")
print("All checks done.")
