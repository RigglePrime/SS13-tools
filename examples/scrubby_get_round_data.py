# flake8: noqa
# pylint: skip-file

import asyncio
from ss13_tools.scrubby import get_multiple_round_json

round_ids = list(range(200000, 200010))

async def main():
    data = [d async for d in get_multiple_round_json(round_ids)]
    print(data)

asyncio.run(main())
