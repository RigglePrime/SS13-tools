# flake8: noqa
# pylint: skip-file

import asyncio

from ss13_tools.scrubby import GetReceipts

receipts = asyncio.run(GetReceipts(ckey="player_name_here", number_of_rounds=10, only_played=True))
for round_played in receipts:
    print(f"{round_played.name} {round_played.job}")
